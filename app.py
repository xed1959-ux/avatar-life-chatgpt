import os
import uuid

from flask import Flask, request, jsonify, Response
from google import genai


app = Flask(__name__)


# =========================================================
# GEMINI
# =========================================================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY is not set")

client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"


# =========================================================
# KESKUSTELUMUISTI
#
# session_id -> viimeisin Gemini interaction ID
# =========================================================

sessions = {}


# =========================================================
# HTML-KÄYTTÖLIITTYMÄ
# =========================================================

HTML_PAGE = r"""
<!DOCTYPE html>

<html lang="fi">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>Avatar Life Gemini</title>


<style>

/* =====================================================
   PERUSASETUKSET
   ===================================================== */

* {
    box-sizing: border-box;
}


html,
body {

    margin: 0;
    padding: 0;

    width: 100%;
    height: 100%;

    background: #111;

    color: #eee;

    font-family:
        Arial,
        Helvetica,
        sans-serif;
}


body {

    display: flex;

    justify-content: center;
    align-items: center;

}


/* =====================================================
   KOKO CHAT
   ===================================================== */

#chat {

    width: 100%;
    height: 100vh;

    max-width: 900px;

    display: flex;

    flex-direction: column;

    background: #181818;

}


/* =====================================================
   YLÄPALKKI
   ===================================================== */

#header {

    height: 42px;
    min-height: 42px;

    padding: 4px 9px;

    background: #222;

    border-bottom:
        1px solid #333;

    display: flex;

    justify-content:
        space-between;

    align-items: center;

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

    padding:
        0 8px;

    font-size: 11px;

}


/* =====================================================
   SUURI KESKUSTELUALUE
   ===================================================== */

#messages {

    flex: 1;

    min-height: 0;

    overflow-y: auto;

    padding: 12px;

    display: flex;

    flex-direction: column;

    gap: 10px;

}


/* =====================================================
   VIESTIT
   ===================================================== */

.message {

    max-width: 85%;

    padding:
        9px 12px;

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

    border:
        1px solid #3a3a3a;

}


.system {

    align-self: center;

    color: #888;

    font-size: 11px;

    text-align: center;

}


/* =====================================================
   ALAPALKKI
   ===================================================== */

#inputArea {

    height: 58px;
    min-height: 58px;

    padding:
        7px 9px;

    background: #222;

    border-top:
        1px solid #333;

    display: flex;

    gap: 7px;

}


/* =====================================================
   TEKSTIKENTTÄ
   ===================================================== */

#messageInput {

    flex: 1;

    width: 100%;

    height: 43px;
    min-height: 43px;
    max-height: 43px;

    resize: none;

    padding:
        9px 11px;

    border:
        1px solid #444;

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


/* =====================================================
   PAINIKKEET
   ===================================================== */

button {

    border: none;

    border-radius: 7px;

    background: #444;

    color: white;

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


#sendButton {

    width: 75px;

    min-width: 75px;

    font-size: 13px;

}


/* =====================================================
   PIENI NÄYTTÖ
   ===================================================== */

@media
(max-width: 500px) {

    #header {

        font-size: 14px;

    }


    #status {

        display: none;

    }


    #newChat {

        font-size: 10px;

    }


    .message {

        max-width: 92%;

        font-size: 14px;

    }


    #sendButton {

        width: 62px;

        min-width: 62px;

    }

}

</style>

</head>


<body>


<div id="chat">


    <!-- ================================================
         YLÄPALKKI
         ================================================ -->

    <div id="header">

        <span>
            Gemini
        </span>


        <div id="headerRight">

            <span id="status">
                Valmis
            </span>


            <button
                id="newChat"
                type="button"
            >
                Uusi
            </button>

        </div>

    </div>


    <!-- ================================================
         KESKUSTELU
         ================================================ -->

    <div id="messages"></div>


    <!-- ================================================
         ALAPALKKI
         ================================================ -->

    <div id="inputArea">


        <textarea
            id="messageInput"
            placeholder="Kirjoita viesti..."
            autocomplete="off"
        ></textarea>


        <button
            id="sendButton"
            type="button"
        >
            Lähetä
        </button>


    </div>


</div>


<script>


// =======================================================
// ELEMENTIT
// =======================================================

const messages =
    document.getElementById(
        "messages"
    );


const input =
    document.getElementById(
        "messageInput"
    );


const sendButton =
    document.getElementById(
        "sendButton"
    );


const newChatButton =
    document.getElementById(
        "newChat"
    );


const statusText =
    document.getElementById(
        "status"
    );


// =======================================================
// SESSION
// =======================================================

const SESSION_KEY =
    "avatar_life_gemini_session";


const INACTIVITY_LIMIT =
    5 * 60 * 1000;


let sessionId =
    localStorage.getItem(
        SESSION_KEY
    );


let lastActivity =
    Date.now();


// =======================================================
// VIESTIN LISÄYS
// =======================================================

function addMessage(
    text,
    type
) {

    const div =
        document.createElement(
            "div"
        );


    div.className =
        "message " + type;


    div.textContent =
        text;


    messages.appendChild(
        div
    );


    messages.scrollTop =
        messages.scrollHeight;

}


// =======================================================
// SYSTEM-VIESTI
// =======================================================

function addSystemMessage(
    text
) {

    addMessage(
        text,
        "system"
    );

}


// =======================================================
// UUSI KESKUSTELU
// =======================================================

function startNewSession() {

    sessionId =
        crypto.randomUUID();


    localStorage.setItem(
        SESSION_KEY,
        sessionId
    );


    messages.innerHTML =
        "";


    addSystemMessage(
        "Uusi Gemini-keskustelu."
    );


    lastActivity =
        Date.now();


    statusText.textContent =
        "Valmis";


    input.focus();

}


// =======================================================
// AKTIIVISUUS
// =======================================================

function registerActivity() {

    lastActivity =
        Date.now();

}


// =======================================================
// VIESTIN LÄHETYS
// =======================================================

async function sendMessage() {

    const message =
        input.value.trim();


    if (!message) {

        return;

    }


    registerActivity();


    addMessage(
        message,
        "user"
    );


    input.value =
        "";


    sendButton.disabled =
        true;


    statusText.textContent =
        "Gemini...";


    try {

        const response =
            await fetch(
                "/chat",
                {

                    method:
                        "POST",

                    headers:
                        {
                            "Content-Type":
                                "application/json"
                        },

                    body:
                        JSON.stringify(
                            {
                                session_id:
                                    sessionId,

                                message:
                                    message
                            }
                        )
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Palvelinvirhe"
            );

        }


        // ---------------------------------------------
        // SESSION ID
        // ---------------------------------------------

        if (data.session_id) {

            sessionId =
                data.session_id;


            localStorage.setItem(
                SESSION_KEY,
                sessionId
            );

        }


        // ---------------------------------------------
        // GEMINI-VASTAUS
        // ---------------------------------------------

        addMessage(
            data.reply,
            "gemini"
        );


        statusText.textContent =
            "Valmis";


        registerActivity();

    }


    catch (error) {

        addSystemMessage(
            "Virhe: " +
            error.message
        );


        statusText.textContent =
            "Virhe";

    }


    finally {

        sendButton.disabled =
            false;


        input.focus();

    }

}


// =======================================================
// SEND-PAINIKE
// =======================================================

sendButton.addEventListener(
    "click",
    sendMessage
);


// =======================================================
// UUSI KESKUSTELU
// =======================================================

newChatButton.addEventListener(
    "click",
    startNewSession
);


// =======================================================
// ENTER
// =======================================================

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


// =======================================================
// AKTIIVISUUS
// =======================================================

input.addEventListener(
    "input",
    registerActivity
);


document.addEventListener(
    "click",
    registerActivity
);


// =======================================================
// 5 MINUUTIN AIKAKATKAISU
// =======================================================

setInterval(
    function() {

        const elapsed =
            Date.now() -
            lastActivity;


        if (
            elapsed >=
            INACTIVITY_LIMIT
        ) {

            if (sessionId) {

                sessionId =
                    null;


                localStorage.removeItem(
                    SESSION_KEY
                );


                messages.innerHTML =
                    "";


                addSystemMessage(
                    "Yhteys suljettiin 5 minuutin käyttämättömyyden jälkeen."
                );


                addSystemMessage(
                    "Kirjoita viesti aloittaaksesi uuden keskustelun."
                );


                statusText.textContent =
                    "Yhteys suljettu";

            }


            lastActivity =
                Date.now();

        }

    },
    10000
);


// =======================================================
// KÄYNNISTYS
// =======================================================

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

    return Response(
        HTML_PAGE,
        mimetype="text/html"
    )


# =========================================================
# CHAT API
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data =
            request.get_json(
                silent=True
            ) or {}


        # ---------------------------------------------
        # HUOM:
        # Oletusarvot "" estävät NoneType.strip()
        # -virheen.
        # ---------------------------------------------

        raw_message =
            data.get(
                "message",
                ""
            )


        raw_session_id =
            data.get(
                "session_id",
                ""
            )


        message =
            raw_message.strip()


        session_id =
            raw_session_id.strip()


        print(
            "Received message:",
            message
        )


        print(
            "Session ID:",
            session_id
        )


        # ---------------------------------------------
        # VIESTI PUUTTUU
        # ---------------------------------------------

        if not message:

            return jsonify(
                {
                    "error":
                        "No message received."
                }
            ), 400


        # ---------------------------------------------
        # UUSI SESSION
        # ---------------------------------------------

        if not session_id:

            session_id =
                str(
                    uuid.uuid4()
                )


            print(
                "Created new session:",
                session_id
            )


        # ---------------------------------------------
        # EDELLINEN GEMINI-KESKUSTELU
        # ---------------------------------------------

        previous_interaction_id =
            sessions.get(
                session_id
            )


        print(
            "Previous interaction:",
            previous_interaction_id
        )


        # ---------------------------------------------
        # GEMINI
        # ---------------------------------------------

        if previous_interaction_id:

            interaction =
                client.interactions.create(
                    model=MODEL,

                    input=message,

                    previous_interaction_id=
                        previous_interaction_id
                )

        else:

            interaction =
                client.interactions.create(
                    model=MODEL,

                    input=message
                )


        # ---------------------------------------------
        # VASTAUS
        # ---------------------------------------------

        reply =
            interaction.output_text


        # ---------------------------------------------
        # TALLENNA VIIMEISIN INTERACTION
        # ---------------------------------------------

        sessions[
            session_id
        ] = interaction.id


        print(
            "Gemini reply:",
            reply
        )


        print(
            "New interaction:",
            interaction.id
        )


        return jsonify(
            {
                "reply":
                    reply,

                "session_id":
                    session_id
            }
        )


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


        return jsonify(
            {
                "error":
                    str(e)
            }
        ), 500


# =========================================================
# UUSI SESSION
# =========================================================

@app.route(
    "/new_session",
    methods=["POST"]
)
def new_session():

    session_id =
        str(
            uuid.uuid4()
        )


    return jsonify(
        {
            "session_id":
                session_id
        }
    )


# =========================================================
# KÄYNNISTYS
# =========================================================

if __name__ == "__main__":

    port =
        int(
            os.environ.get(
                "PORT",
                10000
            )
        )


    app.run(
        host="0.0.0.0",
        port=port
    )
