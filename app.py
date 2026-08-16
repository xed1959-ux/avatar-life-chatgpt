import os
import uuid

from flask import Flask, request, jsonify, Response
from google import genai

app = Flask(__name__)

# ---------------------------------------------------------
# GEMINI
# ---------------------------------------------------------

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

# session_id -> viimeisin Gemini interaction ID
sessions = {}


# ---------------------------------------------------------
# HTML CHAT INTERFACE
# ---------------------------------------------------------

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="fi">

<head>

<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Avatar Life Gemini</title>

<style>

<style>

* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #111;
    color: #eee;
    font-family: Arial, Helvetica, sans-serif;
}

body {
    display: flex;
    justify-content: center;
    align-items: center;
}

#chat {
    width: 100%;
    max-width: 900px;
    height: 100vh;

    display: flex;
    flex-direction: column;

    background: #181818;
}

/* -------------------------
   YLÄPALKKI
   ------------------------- */

#header {
    height: 42px;
    min-height: 42px;

    padding: 5px 10px;

    background: #222;
    border-bottom: 1px solid #333;

    font-size: 16px;
    font-weight: bold;

    display: flex;
    justify-content: space-between;
    align-items: center;
}

#status {
    font-size: 11px;
    font-weight: normal;
    color: #888;
}

#newChat {
    padding: 5px 8px;
    font-size: 11px;
}


/* -------------------------
   KESKUSTELUALUE
   ------------------------- */

#messages {
    flex: 1;

    overflow-y: auto;

    padding: 12px;

    display: flex;
    flex-direction: column;

    gap: 10px;
}


/* -------------------------
   VIESTIT
   ------------------------- */

.message {
    max-width: 85%;

    padding: 9px 12px;

    border-radius: 8px;

    line-height: 1.4;

    white-space: pre-wrap;
    word-wrap: break-word;
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


/* -------------------------
   ALAPALKKI
   ------------------------- */

#inputArea {
    height: 58px;
    min-height: 58px;

    padding: 7px 9px;

    background: #222;

    border-top: 1px solid #333;

    display: flex;

    gap: 7px;
}


/* -------------------------
   TEKSTIKENTTÄ
   ------------------------- */

#messageInput {
    flex: 1;

    min-height: 42px;
    height: 42px;
    max-height: 42px;

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


/* -------------------------
   LÄHETÄ-PAINIKE
   ------------------------- */

button {
    border: none;

    border-radius: 7px;

    padding: 0 14px;

    background: #444;

    color: white;

    font-size: 13px;

    cursor: pointer;
}

button:hover {
    background: #555;
}

button:disabled {
    background: #292929;

    color: #666;

    cursor: default;
}

</style>

</style>

</head>

<body>

<div id="chat">

    <div id="header">
        <span>Gemini</span>

        <div>
            <span id="status">Valmis</span>
            <button id="newChat">Uusi keskustelu</button>
        </div>
    </div>

    <div id="messages"></div>

    <div id="inputArea">

        <textarea
            id="messageInput"
            placeholder="Kirjoita viesti..."
            autocomplete="off"></textarea>

        <button id="sendButton">Lähetä</button>

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


// ---------------------------------------------------------
// MESSAGE DISPLAY
// ---------------------------------------------------------

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


// ---------------------------------------------------------
// NEW SESSION
// ---------------------------------------------------------

function startNewSession() {

    sessionId = crypto.randomUUID();

    localStorage.setItem(
        SESSION_KEY,
        sessionId
    );

    messages.innerHTML = "";

    addSystemMessage(
        "Uusi Gemini-keskustelu."
    );

    lastActivity = Date.now();

    statusText.textContent = "Uusi keskustelu";

    input.focus();
}


// ---------------------------------------------------------
// ACTIVITY
// ---------------------------------------------------------

function registerActivity() {

    lastActivity = Date.now();

}


// ---------------------------------------------------------
// SEND MESSAGE
// ---------------------------------------------------------

async function sendMessage() {

    const message = input.value.trim();

    if (!message) {
        return;
    }

    registerActivity();

    addMessage(message, "user");

    input.value = "";

    sendButton.disabled = true;

    statusText.textContent = "Gemini vastaa...";

    try {

        const response = await fetch(
            "/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    session_id: sessionId,
                    message: message
                })
            }
        );


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Palvelinvirhe"
            );

        }


        // Jos palvelin antoi uuden session ID:n
        if (data.session_id) {

            sessionId = data.session_id;

            localStorage.setItem(
                SESSION_KEY,
                sessionId
            );

        }


        addMessage(
            data.reply,
            "gemini"
        );


        statusText.textContent =
            "Yhteys toimii";


        registerActivity();

    }

    catch (error) {

        addSystemMessage(
            "Virhe: " + error.message
        );

        statusText.textContent =
            "Virhe";

    }

    finally {

        sendButton.disabled = false;

        input.focus();

    }
}


// ---------------------------------------------------------
// BUTTON
// ---------------------------------------------------------

sendButton.addEventListener(
    "click",
    sendMessage
);


newChatButton.addEventListener(
    "click",
    startNewSession
);


// ---------------------------------------------------------
// ENTER
// ---------------------------------------------------------

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


// ---------------------------------------------------------
// ACTIVITY EVENTS
// ---------------------------------------------------------

input.addEventListener(
    "input",
    registerActivity
);

document.addEventListener(
    "click",
    registerActivity
);


// ---------------------------------------------------------
// FIVE MINUTE TIMEOUT
// ---------------------------------------------------------

setInterval(
    function() {

        const elapsed =
            Date.now() - lastActivity;


        if (
            elapsed >=
            INACTIVITY_LIMIT
        ) {

            if (
                sessionId !== null
            ) {

                sessionId = null;

                localStorage.removeItem(
                    SESSION_KEY
                );

                messages.innerHTML = "";

                addSystemMessage(
                    "Yhteys suljettiin 5 minuutin käyttämättömyyden jälkeen."
                );

                addSystemMessage(
                    "Kirjoita uusi viesti aloittaaksesi uuden keskustelun."
                );

                statusText.textContent =
                    "Yhteys suljettu";

            }

            lastActivity = Date.now();

        }

    },
    10000
);


// ---------------------------------------------------------
// INITIALIZE
// ---------------------------------------------------------

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


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.route("/")
def home():

    return Response(
        HTML_PAGE,
        mimetype="text/html"
    )


# ---------------------------------------------------------
# CHAT
# ---------------------------------------------------------

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json(
            silent=True
        ) or {}

        message = data.get(
            "message",
            ""
        ).strip()

        session_id = data.get(
            "session_id",
            ""
        ).strip()


        print(
            "Received message:",
            message
        )

        print(
            "Session ID:",
            session_id
        )


        if not message:

            return jsonify({
                "error":
                "No message received."
            }), 400


        if not session_id:

            session_id = str(
                uuid.uuid4()
            )

            print(
                "Created new session:",
                session_id
            )


        previous_interaction_id = \
            sessions.get(session_id)


        print(
            "Previous interaction:",
            previous_interaction_id
        )


        if previous_interaction_id:

            interaction = \
                client.interactions.create(
                    model=MODEL,
                    input=message,
                    previous_interaction_id=
                        previous_interaction_id
                )

        else:

            interaction = \
                client.interactions.create(
                    model=MODEL,
                    input=message
                )


        reply = interaction.output_text


        sessions[session_id] = \
            interaction.id


        print(
            "Gemini reply:",
            reply
        )

        print(
            "New interaction:",
            interaction.id
        )


        return jsonify({

            "reply": reply,

            "session_id":
                session_id

        })


    except Exception as e:

        print(
            "========== GEMINI ERROR =========="
        )

        print(
            type(e).__name__
        )

        print(
            str(e)
        )

        print(
            "=================================="
        )


        return jsonify({

            "error":
                str(e)

        }), 500


# ---------------------------------------------------------
# NEW SESSION
# ---------------------------------------------------------

@app.route(
    "/new_session",
    methods=["POST"]
)
def new_session():

    session_id = str(
        uuid.uuid4()
    )

    return jsonify({

        "session_id":
            session_id

    })


# ---------------------------------------------------------
# START
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
