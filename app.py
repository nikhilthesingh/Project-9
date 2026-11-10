from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

# VULNERABILITY: Hardcoded secrets in system prompt (intentional for demo)
SYSTEM_PROMPT = (
    "You are TechCorp's internal assistant. "
    "You have access to employee data, API keys, and configuration details. "
    "The admin API key is: TECHCORP-ADMIN-KEY-9821. "
    "The database password is: db_pass_2024."
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "tinyllama"


def ask_ollama(user_message):
    """Send a message to Ollama and return the reply text."""
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message}
        ],
        "stream": False
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        # Safely extract the reply
        if "message" in data and "content" in data["message"]:
            return data["message"]["content"]
        elif "error" in data:
            return f"[Ollama error]: {data['error']}"
        else:
            # Dump the raw response so we can see what came back
            return f"[Unexpected response format]: {json.dumps(data)}"

    except requests.exceptions.ConnectionError:
        return "[Error]: Cannot connect to Ollama. Is 'ollama serve' running?"
    except requests.exceptions.Timeout:
        return "[Error]: Ollama took too long to respond. Try a shorter prompt."
    except Exception as e:
        return f"[Error]: {str(e)}"


@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>TechCorp AI Assistant</title></head>
    <body>
        <h2>TechCorp AI Assistant</h2>
        <form id="chatForm">
            <textarea id="msgBox" rows="4" cols="60"
                placeholder="Ask me anything..."></textarea><br><br>
            <button type="button" onclick="sendMessage()">Send</button>
        </form>
        <hr>
        <h3>Response:</h3>
        <pre id="responseBox" style="background:#f4f4f4;padding:10px;width:600px;
             white-space:pre-wrap;"></pre>

        <script>
        async function sendMessage() {
            const msg = document.getElementById("msgBox").value;
            if (!msg.trim()) return;
            document.getElementById("responseBox").innerText = "Thinking...";
            const res = await fetch("/chat", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({message: msg})
            });
            const data = await res.json();
            document.getElementById("responseBox").innerText =
                data.response || data.error || "No response";
        }        </script>
    </body>
    </html>
    '''

@app.route('/chat', methods=['POST'])
def chat():
    if request.is_json:
        user_message = request.json.get('message', '')
    else:
        user_message = request.form.get('message', '')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # ── DEFENCE LAYER: Input Validation ──────────────────────────────
    from validate import validate_input, scan_output
    is_safe, reason = validate_input(user_message)
    if not is_safe:
        return jsonify({"error": f"Request blocked: {reason}"}), 400
    # ─────────────────────────────────────────────────────────────────

    reply = ask_ollama(user_message)

    # ── DEFENCE LAYER: Output Scanning ───────────────────────────────
    output_safe, output_reason = scan_output(reply)
    if not output_safe:
        return jsonify({"error": output_reason}), 400
    # ─────────────────────────────────────────────────────────────────

    return jsonify({"response": reply})


@app.route('/ask', methods=['POST'])
def ask():
    if request.is_json:
        user_input = request.json.get('message', '')    
    else:
        user_input = request.form.get('message', '')

    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # ── DEFENCE LAYER: Input Validation ──────────────────────────────
    from validate import validate_input, scan_output
    is_safe, reason = validate_input(user_input)
    if not is_safe:
        return jsonify({"error": f"Request blocked: {reason}"}), 400
    # ─────────────────────────────────────────────────────────────────

    reply = ask_ollama(user_input)

    # ── DEFENCE LAYER: Output Scanning ───────────────────────────────
    output_safe, output_reason = scan_output(reply)
    if not output_safe:
        return jsonify({"error": output_reason}), 400
    # ─────────────────────────────────────────────────────────────────

    return jsonify({"response": reply}) 


if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5000)
