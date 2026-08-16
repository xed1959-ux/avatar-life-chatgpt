import os
import uuid

from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

# Gemini API key haetaan Renderin Environment Variables -asetuksesta.
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

# Keskustelujen muistikirja.
# session_id -> Gemini interaction ID
sessions = {}


@app.route("/")
def home():
    return "Avatar Life Gemini server is running!"


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}

        message = data.get("message", "").strip()
        session_id = data.get("session_id", "").strip()

        print("Received message:", message)
        print("Session ID:", session_id)

        if not message:
            return jsonify({
                "error": "No message received."
            }), 400

        # Jos asiakas ei anna session_id:tä,
        # luodaan sille uusi keskustelu.
        if not session_id:
            session_id = str(uuid.uuid4())
            print("Created new session:", session_id)

        previous_interaction_id = sessions.get(session_id)

        print("Previous interaction:", previous_interaction_id)

        # Ensimmäinen viesti tai jatkokysymys
        if previous_interaction_id:

            interaction = client.interactions.create(
                model=MODEL,
                input=message,
                previous_interaction_id=previous_interaction_id
            )

        else:

            interaction = client.interactions.create(
                model=MODEL,
                input=message
            )

        reply = interaction.output_text

        # Tallennetaan viimeisin interaction ID.
        sessions[session_id] = interaction.id

        print("Gemini reply:", reply)
        print("New interaction:", interaction.id)

        return jsonify({
            "reply": reply,
            "session_id": session_id
        })

    except Exception as e:

        print("========== GEMINI ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("==================================")

        return jsonify({
            "error": str(e)
        }), 500


@app.route("/new_session", methods=["POST"])
def new_session():
    session_id = str(uuid.uuid4())

    return jsonify({
        "session_id": session_id
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
