from flask import Flask, request, Response
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    if not url:
        return "Missing url", 400

    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    return Response(r.content, content_type=r.headers.get('Content-Type'))

if __name__ == "__main__":
    app.run()
