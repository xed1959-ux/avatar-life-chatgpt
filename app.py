from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "Avatar Life ChatGPT server is running!"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    return jsonify({
        "reply": "Palvelin vastaanotti viestin: " + message
    })


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
