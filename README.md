# Inventory Merge Studio

Một web app Flask gọn nhẹ giúp gộp nhiều file Excel "Inventory Update" thành một file duy nhất, tự động chuẩn hoá cột, bỏ qua file tạm và thêm logo UI đẹp mắt.

## Tính năng
- Giao diện web hiện đại, hỗ trợ kéo/thả hoặc chọn nhiều file Excel cùng lúc.
- API `/api/merge` nhận danh sách file Excel, đọc sheet `Worksheet`, chuẩn hoá các cột bắt buộc và thêm cột `source_file` để truy vết.
- Bỏ qua file tạm (bắt đầu bằng `~$`) và thêm cột bị thiếu với giá trị trống.
- Trả về file `Inventory_Merged.xlsx` kèm header `X-Merge-Report` mô tả chi tiết quá trình gộp.

## Chạy ứng dụng

```bash
python -m venv .venv
source .venv/bin/activate  # hoặc .venv\\Scripts\\activate trên Windows
pip install -r requirements.txt
python app.py
```

Ứng dụng chạy tại `http://localhost:5000`. Trang chủ cung cấp form tải file và nút "Gộp & tải xuống" để nhận file Excel đã hợp nhất.
