from flask import Flask, send_from_directory
from settings import SERT_FILE, KEY_FILE

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory("web/", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10001, ssl_context=(SERT_FILE, KEY_FILE))
