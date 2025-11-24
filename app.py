"""Excel inventory merge service with a polished web front-end."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable, List

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


@dataclass(frozen=True)
class MergeConfig:
    target_columns: List[str]
    sheet_name: str = "Worksheet"
    file_pattern: str = "*Inventory Update*.xlsx"
    output_filename: str = "Inventory_Merged.xlsx"


DEFAULT_CONFIG = MergeConfig(
    target_columns=[
        "vendor_sku",
        "vendor_name",
        "Begin",
        "End",
        "Notes",
        "Flag: No Product Feed",
        "Qty",
        "Policy",
    ],
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names by stripping whitespace."""
    updated = df.copy()
    updated.columns = [column.strip() for column in updated.columns]
    return updated


class MergeFailure(RuntimeError):
    """Raised when no valid workbook data could be merged."""


def merge_workbooks(files: Iterable) -> tuple[BytesIO, dict]:
    """
    Merge the provided Excel workbooks into a single Excel file.

    Returns a tuple of (excel_bytes, summary_dict).
    """

    all_frames: list[pd.DataFrame] = []
    details: list[dict] = []

    for uploaded in files:
        filename = secure_filename(uploaded.filename or "unknown.xlsx")
        if filename.startswith("~$"):
            LOGGER.info("Skipping temporary workbook: %s", filename)
            continue

        LOGGER.info("Processing workbook: %s", filename)
        try:
            frame = pd.read_excel(uploaded, sheet_name=DEFAULT_CONFIG.sheet_name, engine="openpyxl")
            frame = normalize_columns(frame)
            missing = [col for col in DEFAULT_CONFIG.target_columns if col not in frame.columns]

            if missing:
                LOGGER.warning("%s missing columns: %s", filename, missing)
                for col in missing:
                    frame[col] = ""

            for col in DEFAULT_CONFIG.target_columns:
                if col not in frame.columns:
                    frame[col] = ""

            frame = frame[DEFAULT_CONFIG.target_columns].copy()
            for col in frame.columns:
                if frame[col].dtype == "datetime64[ns]":
                    frame[col] = frame[col].astype(str).replace("NaT", "")

            frame["source_file"] = filename
            all_frames.append(frame)
            details.append({"file": filename, "rows": len(frame), "missing_columns": missing})
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("Failed to process %s", filename)
            details.append({"file": filename, "error": str(exc)})

    if not all_frames:
        raise MergeFailure("Không có dữ liệu hợp lệ để gộp.")

    merged = pd.concat(all_frames, ignore_index=True)
    buffer = BytesIO()
    merged.to_excel(buffer, index=False)
    buffer.seek(0)

    summary = {
        "total_rows": len(merged),
        "file_count": len(all_frames),
        "details": details,
    }
    return buffer, summary


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            config=DEFAULT_CONFIG,
            columns=DEFAULT_CONFIG.target_columns,
        )

    @app.post("/api/merge")
    def merge_endpoint():
        uploaded_files = request.files.getlist("files")
        if not uploaded_files:
            return jsonify({"error": "Vui lòng chọn ít nhất một file Excel."}), 400

        try:
            buffer, summary = merge_workbooks(uploaded_files)
        except MergeFailure as exc:
            return jsonify({"error": str(exc)}), 400

        response = send_file(
            buffer,
            as_attachment=True,
            download_name=DEFAULT_CONFIG.output_filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response.headers["X-Merge-Report"] = json.dumps(summary, ensure_ascii=False)
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
