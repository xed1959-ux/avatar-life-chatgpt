import os

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

MODEL = "gpt-5.6"


@app.route("/")
def home():
    return "Avatar Life ChatGPT server is running!"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

        if not message:
            return jsonify({
                "error": "No message received."
            }), 400

        response = client.responses.create(
            model=MODEL,
            input=message
        )

        return jsonify({
            "reply": response.output_text
        })

    except Exception as e:
        print("ERROR:", str(e))

        return jsonify({
            "error": "OpenAI request failed."
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
