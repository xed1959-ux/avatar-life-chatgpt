import os

from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

api_key = os.environ.get("OPENAI_API_KEY")

if not api_key:
    print("ERROR: OPENAI_API_KEY is not set")

client = OpenAI(api_key=api_key)

MODEL = "gpt-5.6"


@app.route("/")
def home():
    return "Avatar Life ChatGPT server is running!"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

        print("Received message:", message)

        if not message:
            return jsonify({
                "error": "No message received."
            }), 400

        print("Sending request to OpenAI...")

        response = client.responses.create(
            model=MODEL,
            input=message
        )

        reply = response.output_text

        print("OpenAI reply:", reply)

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        print("========== OPENAI ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==================================")

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
