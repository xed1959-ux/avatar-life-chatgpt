import os

from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)

MODEL = "gemini-2.5-flash"


@app.route("/")
def home():
    return "Avatar Life Gemini server is running!"


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

        print("Sending request to Gemini...")

        response = client.models.generate_content(
            model=MODEL,
            contents=message
        )

        reply = response.text

        print("Gemini reply:", reply)

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        print("========== GEMINI ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==================================")

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
