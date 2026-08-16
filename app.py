import os
import uuid
from flask import Flask, request, jsonify, Response
from google import genai

app = Flask(__name__)

# =========================================================
# GEMINI
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY puuttuu Renderistä.")

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = "gemini-3.5-flash"


# =========================================================
# KESKUSTELUMUISTI
# session_id -> viimeisin Gemini interaction ID
# =========================================================

sessions = {}


# =========================================================
# HTML
# =========================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="fi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Gemini</title>

<style>

* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #111;
    color: #eee;
    font-family: Arial, Helvetica, sans-serif;
}

body {
    width: 100%;
    height: 100%;
}

#chat {
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    background: #181818;
}


/* YLÄPALKKI */

#header {
    height: 10%;
    min-height: 0;
    padding: 2px 8px;
    background: #222;
    border-bottom: 1px solid #333;

    display: flex;
    align-items: center;
    justify-content: space-between;

    font-size: 16px;
    font-weight: bold;
}

#headerRight {
    display: flex;
    align-items: center;
    gap: 7px;
}

#status {
    font-size: 11px;
    font-weight: normal;
    color: #888;
}

#newChat {
    height: 27px;
    padding: 0 9px;
    border: 0;
    border-radius: 6px;
    background: #444;
    color: white;
    font-size: 11px;
    cursor: pointer;
}


/* KESKUSTELUALUE */

#messages {
    height: 80%;
    flex: none;
    min-height: 0;

    overflow-y: auto;

    padding: 12px;

    display: flex;
    flex-direction: column;
    gap: 10px;
}


/* VIESTIT */

.message {
    max-width: 85%;
    padding: 9px 12px;
    border-radius: 8px;

    line-height: 1.4;

    white-space: pre-wrap;
    word-wrap: break-word;

    font-size: 15px;
}

.user {
    align-self: flex-end;
    background: #315b8a;
    color: white;
}

.gemini {
    align-self: flex-start;
    background: #292929;
    border: 1px solid #3a3a3a;
}

.system {
    align-self: center;
    color: #888;
    font-size: 11px;
    text-align: center;
}


/* ALAPALKKI */

#inputArea {
    height: 10%;
    min-height: 0;

    padding: 6px 8px;

    background: #222;
    border-top: 1px solid #333;

    display: flex;
    gap: 7px;
}


/* TEKSTIKENTTÄ */

#messageInput {
    flex: 1;

    width: 100%;
    height: 43px;
    min-height: 43px;
    max-height: 43px;

    resize: none;

    padding: 9px 11px;

    border: 1px solid #444;
    border-radius: 7px;

    background: #111;
    color: #eee;

    font-size: 15px;
    font-family: inherit;

    outline: none;
}

#messageInput:focus {
    border-color: #666;
}


/* LÄHETÄ */

#sendButton {
    width: 72px;
    min-width: 72px;

    border: 0;
    border-radius: 7px;

    background: #444;
    color: white;

    font-size: 13px;
    cursor: pointer;
}

#sendButton:hover,
#newChat:hover {
    background: #555;
}

#sendButton:disabled {
    background: #292929;
    color: #666;
    cursor: default;
}

</style>
</head>


<body>

<div id="chat">

    <div id="header">

        <span>Gemini</span>

        <div id="headerRight">

            <span id="status">Valmis</span>

            <button id="newChat" type="button">
                Uusi
            </button>

        </div>

    </div>


    <div id="messages"></div>


    <div id="inputArea">

        <textarea
            id="messageInput"
            placeholder="Kirjoita viesti..."
            autocomplete="off"
        ></textarea>

        <button id="sendButton" type="button">
            Lähetä
        </button>

    </div>

</div>


<script>

const messages = document.getElementById("messages");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const newChatButton = document.getElementById("newChat");
const statusText = document.getElementById("status");

const SESSION_KEY = "avatar_life_gemini_session";

const INACTIVITY_LIMIT = 5 * 60 * 1000;

let sessionId = localStorage.getItem(SESSION_KEY);
let lastActivity = Date.now();


function addMessage(text, type) {

    const div = document.createElement("div");

    div.className = "message " + type;

    div.textContent = text;

    messages.appendChild(div);

    messages.scrollTop = messages.scrollHeight;
}


function addSystemMessage(text) {

    addMessage(text, "system");

}


function startNewSession() {

    sessionId = crypto.randomUUID();

    localStorage.setItem(SESSION_KEY, sessionId);

    messages.innerHTML = "";

    addSystemMessage("Uusi Gemini-keskustelu.");

    lastActivity = Date.now();

    statusText.textContent = "Valmis";

    input.focus();
}


function registerActivity() {

    lastActivity = Date.now();

}


async function sendMessage() {

    const message = input.value.trim();

    if (!message) {
        return;
    }

    registerActivity();

    addMessage(message, "user");

    input.value = "";

    sendButton.disabled = true;

    statusText.textContent = "Gemini...";


    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                session_id: sessionId,
                message: message
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error || "Palvelinvirhe"
            );

        }


        if (data.session_id) {

            sessionId = data.session_id;

            localStorage.setItem(
                SESSION_KEY,
                sessionId
            );

        }


        addMessage(data.reply, "gemini");

        statusText.textContent = "Valmis";

        registerActivity();

    }

    catch (error) {

        addSystemMessage(
            "Virhe: " + error.message
        );

        statusText.textContent = "Virhe";

    }

    finally {

        sendButton.disabled = false;

        input.focus();

    }

}


sendButton.addEventListener(
    "click",
    sendMessage
);


newChatButton.addEventListener(
    "click",
    startNewSession
);


input.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();

        }

    }
);


input.addEventListener(
    "input",
    registerActivity
);


setInterval(
    function() {

        if (
            sessionId &&
            Date.now() - lastActivity >= INACTIVITY_LIMIT
        ) {

            sessionId = null;

            localStorage.removeItem(SESSION_KEY);

            messages.innerHTML = "";

            addSystemMessage(
                "Yhteys suljettiin 5 minuutin käyttämättömyyden jälkeen."
            );

            addSystemMessage(
                "Kirjoita viesti aloittaaksesi uuden keskustelun."
            );

            statusText.textContent = "Yhteys suljettu";

            lastActivity = Date.now();

        }

    },
    10000
);


if (!sessionId) {

    startNewSession();

}

else {

    addSystemMessage(
        "Aiempi keskustelu on valmis jatkumaan."
    );

}

input.focus();

</script>

</body>
</html>
"""


# =========================================================
# ETUSIVU
# =========================================================

@app.route("/")
def home():
    return Response(HTML_PAGE, mimetype="text/html")


# =========================================================
# CHAT
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(silent=True) or {}

        if not isinstance(data, dict):
            data = {}


        message = str(data.get("message") or "").strip()

        session_id = str(data.get("session_id") or "").strip()


        print("Received message:", message)
        print("Session ID:", session_id)


        if not message:

            return jsonify({
                "error": "Viesti puuttuu."
            }), 400


        if not session_id:

            session_id = str(uuid.uuid4())

            print(
                "Created new session:",
                session_id
            )


        previous_interaction = sessions.get(session_id)

        print(
            "Previous interaction:",
            previous_interaction
        )


        # ---------------------------------------------
        # GEMINI
        # ---------------------------------------------

        if previous_interaction:

            interaction = client.interactions.create(
                model=MODEL,
                input=message,
                previous_interaction_id=previous_interaction
            )

        else:

            interaction = client.interactions.create(
                model=MODEL,
                input=message
            )


        reply = interaction.output_text


        sessions[session_id] = interaction.id


        print("Gemini reply:", reply)

        print(
            "New interaction:",
            interaction.id
        )


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


# =========================================================
# NEW SESSION
# =========================================================

@app.route("/new_session", methods=["POST"])
def create_new_session():

    session_id = str(uuid.uuid4())

    return jsonify({
        "session_id": session_id
    })


# =========================================================
# KÄYNNISTYS
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
