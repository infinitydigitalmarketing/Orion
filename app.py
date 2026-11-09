from flask import Flask, render_template_string, request
import os
from groq import Groq

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ORION // PERSONAL AI HUD</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            background: #000308; 
            color: #e2e8f0; 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            overflow: hidden;
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(0, 150, 255, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(0, 220, 255, 0.1) 0%, transparent 40%),
                linear-gradient(135deg, #000206 0%, #010814 100%);
        }
        
        .hud-wrapper {
            width: 97%;
            max-width: 1420px;
            height: 92vh;
            background: linear-gradient(135deg, rgba(2, 12, 28, 0.92) 0%, rgba(1, 6, 15, 0.97) 100%);
            border: 2px solid rgba(0, 212, 255, 0.6);
            border-radius: 26px;
            box-shadow: 
                0 0 50px rgba(0, 180, 255, 0.25),
                0 0 100px rgba(0, 140, 255, 0.15) inset,
                0 0 20px rgba(0, 212, 255, 0.4) inset;
            display: flex;
            position: relative;
            overflow: hidden;
        }

        .hud-wrapper::after {
            content: '';
            position: absolute;
            top: 0; right: 0;
            border-style: solid;
            border-width: 0 65px 65px 0;
            border-color: transparent rgba(0, 212, 255, 0.9) transparent transparent;
            z-index: 10;
            filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.8));
        }

        .sidebar {
            width: 310px;
            background: linear-gradient(180deg, rgba(1, 7, 16, 0.98) 0%, rgba(1, 4, 10, 0.99) 100%);
            border-right: 1px solid rgba(0, 212, 255, 0.35);
            display: flex;
            flex-direction: column;
            padding: 30px 22px;
            gap: 26px;
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.6);
            z-index: 2;
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .brand-ring {
            width: 54px;
            height: 54px;
            border: 2px solid #00d4ff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.85), inset 0 0 10px rgba(0, 212, 255, 0.5);
            background: radial-gradient(circle, rgba(0, 212, 255, 0.3) 0%, rgba(0, 100, 200, 0.1) 100%);
        }

        .brand-text h1 {
            margin: 0;
            font-size: 21px;
            color: #ffffff;
            letter-spacing: 2.5px;
            font-weight: 900;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }

        .brand-text span {
            font-size: 10px;
            color: #00d4ff;
            letter-spacing: 3px;
            font-weight: 800;
        }

        .menu-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-top: 14px;
        }

        .menu-item {
            padding: 16px 20px;
            border-radius: 14px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            gap: 16px;
            border: 1px solid transparent;
        }

        .menu-item.active, .menu-item:hover {
            background: linear-gradient(90deg, rgba(0, 212, 255, 0.25) 0%, rgba(0, 120, 255, 0.05) 100%);
            color: #00d4ff;
            border-left: 4px solid #00d4ff;
            border-color: rgba(0, 212, 255, 0.3);
            box-shadow: inset 0 0 15px rgba(0, 212, 255, 0.2), 0 0 15px rgba(0, 212, 255, 0.1);
        }

        .globe-module {
            margin-top: auto;
            background: linear-gradient(135deg, rgba(0, 212, 255, 0.08) 0%, rgba(0, 100, 200, 0.02) 100%);
            border: 1px solid rgba(0, 212, 255, 0.4);
            border-radius: 18px;
            padding: 20px 16px;
            text-align: center;
            box-shadow: inset 0 0 25px rgba(0, 212, 255, 0.1), 0 0 20px rgba(0, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }

        .globe-icon-ring {
            width: 82px;
            height: 82px;
            margin: 0 auto 12px auto;
            border: 2px dashed rgba(0, 212, 255, 0.8);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #00d4ff;
            font-size: 30px;
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.5), inset 0 0 15px rgba(0, 212, 255, 0.3);
            background: rgba(0, 212, 255, 0.05);
            animation: spinGlobe 15s linear infinite;
        }

        @keyframes spinGlobe { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

        .workspace-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 28px 34px;
            background: linear-gradient(135deg, rgba(1, 5, 12, 0.5) 0%, rgba(2, 10, 22, 0.75) 100%);
            position: relative;
        }

        .top-command-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            border-bottom: 1px solid rgba(0, 212, 255, 0.35);
            padding-bottom: 20px;
            position: relative;
        }

        .ai-center-header {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 16px;
            background: linear-gradient(135deg, rgba(2, 12, 28, 0.95) 0%, rgba(1, 6, 16, 0.95) 100%);
            padding: 8px 30px;
            border-radius: 60px;
            border: 2px solid rgba(0, 212, 255, 0.6);
            box-shadow: 0 0 35px rgba(0, 212, 255, 0.4), inset 0 0 15px rgba(0, 212, 255, 0.2);
        }

        .ai-avatar-hud {
            width: 58px;
            height: 58px;
            background: radial-gradient(circle, rgba(0, 212, 255, 0.4) 0%, rgba(0, 100, 200, 0.2) 100%);
            border: 2px solid #00d4ff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #00d4ff;
            font-size: 28px;
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.8), inset 0 0 10px rgba(0, 212, 255, 0.6);
            position: relative;
        }

        .ai-details h2 {
            margin: 0;
            font-size: 20px;
            color: #ffffff;
            letter-spacing: 2.5px;
            font-weight: 900;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.6);
        }

        .ai-details p { margin: 3px 0 0 0; font-size: 11.5px; color: #94a3b8; letter-spacing: 0.5px; font-weight: 600; }

        .status-actions {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-left: auto;
        }

        .online-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13.5px;
            color: #22c55e;
            background: rgba(34, 197, 94, 0.15);
            padding: 9px 20px;
            border-radius: 30px;
            border: 1.5px solid rgba(34, 197, 94, 0.5);
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.35), inset 0 0 8px rgba(34, 197, 94, 0.2);
            font-weight: 800;
        }

        .live-dot {
            width: 10px;
            height: 10px;
            background: #22c55e;
            border-radius: 50%;
            box-shadow: 0 0 12px #22c55e;
        }

        .user-avatar-btn {
            width: 46px;
            height: 46px;
            border: 2px solid rgba(0, 212, 255, 0.7);
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 212, 255, 0.25) 0%, rgba(0, 100, 200, 0.1) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #00d4ff;
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.5), inset 0 0 8px rgba(0, 212, 255, 0.3);
        }

        .chat-view { 
            flex: 1; 
            overflow-y: auto; 
            padding: 24px; 
            border: 1.5px solid rgba(0, 212, 255, 0.4); 
            border-radius: 20px; 
            margin-bottom: 24px; 
            background: linear-gradient(135deg, rgba(1, 3, 8, 0.95) 0%, rgba(0, 2, 5, 0.98) 100%); 
            display: flex; 
            flex-direction: column; 
            gap: 18px; 
            box-shadow: inset 0 0 45px rgba(0, 0, 0, 0.95), 0 0 20px rgba(0, 212, 255, 0.05);
        }

        .message { 
            padding: 16px 22px; 
            border-radius: 16px; 
            max-width: 75%; 
            line-height: 1.55; 
            font-size: 14.5px;
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        .user { 
            background: linear-gradient(135deg, #0088ff 0%, #0055cc 100%); 
            color: #fff; 
            align-self: flex-end; 
            border-bottom-right-radius: 4px;
            box-shadow: 0 5px 20px rgba(0, 136, 255, 0.45);
        }

        .orion { 
            background: linear-gradient(135deg, rgba(12, 30, 55, 0.95) 0%, rgba(6, 18, 35, 0.98) 100%); 
            color: #e2e8f0; 
            align-self: flex-start; 
            border-bottom-left-radius: 4px;
            border: 1.5px solid rgba(0, 212, 255, 0.5);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.7), inset 0 0 10px rgba(0, 212, 255, 0.1);
        }

        .command-input-bar { 
            display: flex; 
            gap: 16px; 
            background: linear-gradient(135deg, rgba(2, 10, 22, 0.98) 0%, rgba(1, 5, 12, 0.99) 100%);
            padding: 12px 16px;
            border: 2px solid rgba(0, 212, 255, 0.6);
            border-radius: 18px;
            box-shadow: 0 0 35px rgba(0, 212, 255, 0.25), inset 0 0 15px rgba(0, 212, 255, 0.08);
        }

        .file-attach-btn {
            background: transparent;
            border: none;
            color: #00d4ff;
            font-size: 24px;
            cursor: pointer;
            padding: 0 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: opacity 0.2s;
            filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.5));
        }

        .file-attach-btn:hover { opacity: 0.7; }

        input[type="text"] { 
            flex: 1; 
            padding: 14px 18px; 
            border-radius: 12px; 
            border: none; 
            background: transparent; 
            color: #fff; 
            font-size: 15.5px; 
            outline: none;
        }

        input[type="text"]::placeholder { color: #475569; font-weight: 500; }

        .transmit-action-btn { 
            padding: 14px 38px; 
            background: linear-gradient(135deg, #00f3ff 0%, #0066ff 100%); 
            color: #000308; 
            border: none; 
            border-radius: 14px; 
            cursor: pointer; 
            font-weight: 900; 
            font-size: 14.5px;
            letter-spacing: 2.5px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 35px rgba(0, 243, 255, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.5);
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .transmit-action-btn:hover { 
            background: linear-gradient(135deg, #33f5ff 0%, #0088ff 100%);
            box-shadow: 0 0 50px rgba(0, 243, 255, 1), inset 0 0 15px rgba(255, 255, 255, 0.8);
            transform: translateY(-2px);
        }

        @media(max-width: 950px) {
            .sidebar { display: none; }
            .ai-center-header { position: static; transform: none; }
            .hud-wrapper { width: 100%; height: 100vh; border-radius: 0; border: none; }
        }
    </style>
</head>
<body>
    <div class="hud-wrapper">
        <div class="sidebar">
            <div class="brand-box">
                <div class="brand-ring">🌐</div>
                <div class="brand-text">
                    <h1>ORION</h1>
                    <span>PERSONAL AI</span>
                </div>
            </div>
            
            <div class="menu-list">
                <a href="#" class="menu-item active">🏠 Home</a>
                <a href="#" class="menu-item">💬 Chat History</a>
                <a href="#" class="menu-item">⚙️ Settings</a>
                <a href="#" class="menu-item">ℹ️ About</a>
            </div>

            <div class="globe-module">
                <div class="globe-icon-ring">🌍</div>
                <div style="font-size: 11.5px; color: #00d4ff; font-weight: 900; letter-spacing: 2px;">SYSTEM ONLINE</div>
                <div style="font-size: 10.5px; color: #94a3b8; margin-top: 5px; font-weight: 600;">Your AI Assistant<br>Always Here...</div>
            </div>
        </div>

        <div class="workspace-main">
            <div class="top-command-bar">
                <div class="ai-center-header">
                    <div class="ai-avatar-hud">🤖</div>
                    <div class="ai-details">
                        <h2>ORION</h2>
                        <p>Smart • Fast • Always with You</p>
                    </div>
                </div>

                <div class="status-actions">
                    <div class="online-badge">
                        <div class="live-dot"></div>
                        Online
                    </div>
                    <div class="user-avatar-btn">👤</div>
                </div>
            </div>

            <div class="chat-view" id="chatBox">
                <div class="message orion">Hello boss orion here, How may I assist you today?</div>
            </div>

            <form class="command-input-bar" id="chatForm">
                <button type="button" class="file-attach-btn" title="Attach file">📎</button>
                <input type="text" id="userInput" placeholder="Transmit command to Orion..." autocomplete="off" required>
                <button type="submit" class="transmit-action-btn">
                    <span>TRANSMIT</span> ✈️
                </button>
            </form>
        </div>
    </div>

    <script>
        const chatForm = document.getElementById('chatForm');
        const userInput = document.getElementById('userInput');
        const chatBox = document.getElementById('chatBox');

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = userInput.value;
            if(!text) return;

            chatBox.innerHTML += `<div class="message user">${text}</div>`;
            userInput.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();

            chatBox.innerHTML += `<div class="message orion">${data.reply}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        client = Groq(api_key=api_key)
        
        # Updated to llama-3.3-70b-versatile to avoid model not found error
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Orion, an advanced futuristic AI personal assistant. Always reply in clear, professional English."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        reply = f"System Error, Boss: {str(e)}"
    
    return {"reply": reply}

if __name__ == "__main__":
    app.run(debug=True)