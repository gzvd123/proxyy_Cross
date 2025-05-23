from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    return r.text

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
