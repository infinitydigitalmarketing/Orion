from flask import Flask, render_template_string, request, url_for
import os
from groq import Groq
from google import genai
from google.genai import types
from datetime import datetime, timedelta, timezone

app = Flask(__name__)

def find_orion_image():
    """Find the ORION image even if its filename casing/extension differs."""
    static_dir = os.path.join(app.root_path, "static")
    if not os.path.isdir(static_dir):
        app.logger.error("Static directory not found: %s", static_dir)
        return None

    # Exact common names first, then case-insensitive matching for Linux/Vercel.
    candidates = [
        "orion.png", "Orion.png", "ORION.png",
        "orion.png.png", "Orion.png.png", "ORION.png.png",
        "orion.jpg", "Orion.jpg", "orion.jpeg", "Orion.jpeg",
        "orion.webp", "Orion.webp",
    ]
    available = os.listdir(static_dir)
    by_lower = {name.lower(): name for name in available}

    for candidate in candidates:
        actual_name = by_lower.get(candidate.lower())
        if actual_name and os.path.isfile(os.path.join(static_dir, actual_name)):
            app.logger.info("Using ORION image asset: %s", actual_name)
            return actual_name

    app.logger.error("ORION image not found. Files in static/: %s", available)
    return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ORION // PERSONAL AI HUD</title>
<style>
      :root {
        --cyan:#00d9ff; --blue:#087cff; --deep:#020817;
        --line:rgba(0,190,255,.72); --muted:#9fb8df;
      }
      * { box-sizing:border-box; }
      html,body { width:100%; height:100%; min-height:100%; margin:0; }
      body {
        overflow:hidden; color:#edf7ff;
        font-family:Inter,"Segoe UI",Arial,sans-serif;
        background:
          radial-gradient(ellipse at 72% 65%,rgba(0,96,255,.18),transparent 44%),
          radial-gradient(ellipse at 12% 10%,rgba(0,185,255,.12),transparent 30%),
          #01040d;
      }
      button,input { font:inherit; }
      .hud-wrapper {
        display:flex; width:100%; height:100dvh; min-height:0;
        overflow:hidden; position:relative;
        background:linear-gradient(120deg,rgba(2,12,30,.98),rgba(0,4,15,.99));
        border:1px solid rgba(0,174,255,.78);
        box-shadow:0 0 32px rgba(0,145,255,.28),inset 0 0 45px rgba(0,90,255,.08);
      }
      .hud-wrapper::before {
        content:""; position:absolute; inset:0; pointer-events:none; z-index:5;
        background:linear-gradient(90deg,transparent 0%,rgba(0,190,255,.04) 50%,transparent 100%);
      }
      .sidebar {
        flex:0 0 350px; width:350px; min-width:300px; min-height:0;
        display:flex; flex-direction:column; gap:18px;
        padding:22px 18px 16px;
        background:linear-gradient(180deg,rgba(1,8,21,.99),rgba(0,3,12,.99));
        border-right:1px solid rgba(0,180,255,.55);
        box-shadow:12px 0 35px rgba(0,0,0,.45); z-index:2;
      }
      .brand-box { display:flex; align-items:center; gap:15px; padding:4px 4px 22px; border-bottom:1px solid rgba(0,180,255,.25); }
      .brand-ring {
        width:68px; height:68px; flex:0 0 68px; border:2px solid var(--cyan); border-radius:50%;
        display:grid; place-items:center; color:#7ceeff; font-size:29px;
        background:radial-gradient(circle,rgba(0,210,255,.25),rgba(0,50,120,.08));
        box-shadow:0 0 25px rgba(0,190,255,.75),inset 0 0 18px rgba(0,190,255,.28);
      }
      .brand-text h1 { margin:0; color:white; font-size:29px; font-weight:900; letter-spacing:3px; text-shadow:0 0 14px #008dff; }
      .brand-text span { color:var(--cyan); font-size:12px; font-weight:800; letter-spacing:4px; }
      .menu-list { display:flex; flex-direction:column; gap:9px; }
      .menu-item {
        min-height:61px; padding:14px 18px; display:flex; align-items:center; gap:16px;
        color:#b9cbed; text-decoration:none; font-size:18px; font-weight:650;
        border:1px solid rgba(30,115,220,.2); border-radius:15px;
        background:linear-gradient(100deg,rgba(2,22,53,.55),rgba(0,8,25,.35));
        cursor:pointer; transition:.22s ease;
      }
      .menu-item:hover,.menu-item.active {
        color:#5cecff; border-color:#00bfff;
        background:linear-gradient(90deg,rgba(0,180,255,.25),rgba(0,65,150,.12));
        box-shadow:0 0 20px rgba(0,160,255,.24),inset 0 0 18px rgba(0,140,255,.12);
      }
      .clear-history-btn { width:100%; text-align:left; font:inherit; }
      .orion-portrait-card {
        position:relative; flex:0 0 38vh; height:38vh; min-height:235px; max-height:390px;
        margin-top:auto; overflow:hidden; border:1px solid rgba(0,190,255,.8); border-radius:18px;
        background:#020b1c url("{{ url_for('static', filename='earth-space-bg.png') }}?v=2") center 70%/cover no-repeat;
        box-shadow:0 0 24px rgba(0,125,255,.25),inset 0 0 20px rgba(0,150,255,.12);
      }
      .sidebar-orion-image {
        display:block; width:100%; height:100%; object-fit:cover; object-position:center 8%;
        transform:scale(1.13); transform-origin:center 18%;
        filter:saturate(1.16) contrast(1.08);
      }
      .orion-portrait-card::after {
        content:""; position:absolute; inset:48% 0 0;
        background:linear-gradient(transparent 0%,rgba(0,4,16,.78) 100%); pointer-events:none;
      }
      .portrait-caption {
        position:absolute; z-index:2; left:10px; right:10px; bottom:17px;
        text-align:center; color:#8cefff; font-size:22px; line-height:1.15;
        font-weight:850; font-style:italic; text-shadow:0 0 13px #008dff,0 2px 5px #000;
      }
      .portrait-scanline { position:absolute; z-index:3; left:0; right:0; top:0; height:2px; background:#65efff; box-shadow:0 0 13px #00bfff; animation:scan 5s linear infinite; }
      @keyframes scan { from{top:0} to{top:100%} }
      .workspace-main {
        flex:1 1 auto; min-width:0; min-height:0; overflow:hidden;
        display:flex; flex-direction:column; gap:0; padding:20px 26px 20px;
        background:radial-gradient(ellipse at 80% 85%,rgba(0,80,200,.13),transparent 45%),rgba(0,5,17,.38);
      }
      .top-command-bar {
        flex:0 0 105px; min-width:0; display:flex; align-items:center; justify-content:space-between;
        position:relative; margin-bottom:14px; padding:0 5px 14px;
        border-bottom:1px solid rgba(0,160,255,.34);
      }
      .ai-center-header {
        position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
        display:flex; align-items:center; gap:15px; padding:8px 28px 8px 10px;
        border:1px solid rgba(0,190,255,.8); border-radius:18px;
        background:linear-gradient(100deg,rgba(0,24,60,.98),rgba(0,7,24,.97));
        box-shadow:0 0 28px rgba(0,135,255,.28),inset 0 0 18px rgba(0,120,255,.13);
        white-space:nowrap;
      }
      .ai-avatar-hud {
        width:66px; height:66px; flex:0 0 66px; overflow:hidden; border-radius:50%;
        border:2px solid var(--cyan); background:#03132c;
        box-shadow:0 0 23px rgba(0,170,255,.8);
      }
      .ai-avatar-hud img { width:100%; height:100%; object-fit:cover; object-position:center 18%; border-radius:50%; display:block; }
      .ai-details h2 { margin:0; color:#fff; font-size:27px; font-weight:900; letter-spacing:3px; text-shadow:0 0 12px #008dff; }
      .ai-details p { margin:3px 0 0; color:#b7cbed; font-size:13px; font-weight:600; }
      .status-actions { display:flex; align-items:center; gap:16px; margin-left:auto; }
      .online-badge {
        display:flex; align-items:center; gap:9px; padding:10px 19px; border-radius:30px;
        color:#35ed88; font-size:14px; font-weight:800;
        background:rgba(0,255,105,.1); border:1px solid rgba(34,220,120,.55);
        box-shadow:0 0 18px rgba(0,255,105,.17);
      }
      .live-dot { width:10px; height:10px; border-radius:50%; background:#22e879; box-shadow:0 0 12px #22e879; }
      .user-avatar-btn {
        width:51px; height:51px; display:grid; place-items:center; border-radius:50%;
        color:#d8efff; font-size:23px; border:2px solid rgba(0,190,255,.8);
        background:radial-gradient(circle,rgba(0,150,255,.28),rgba(0,30,90,.2));
        box-shadow:0 0 18px rgba(0,150,255,.38);
      }
      .clear-history-top {
        display:none; padding:8px 13px; color:#7ceeff; background:rgba(0,180,255,.08);
        border:1px solid rgba(0,190,255,.45); border-radius:20px; cursor:pointer;
      }
      .chat-view {
        position:relative; isolation:isolate; flex:1 1 0; min-width:0; min-height:0;
        display:flex; flex-direction:column; gap:18px; overflow-y:auto; overflow-x:hidden;
        padding:28px 30px; margin:0 0 14px; border:2px solid rgba(0,155,255,.82);
        border-radius:25px;
        background-color:#010817;
        background-image:linear-gradient(90deg,rgba(0,5,18,.85) 0%,rgba(0,5,18,.45) 55%,rgba(0,5,18,.08) 100%),url("{{ url_for('static', filename='earth-space-bg.png') }}?v=1");
        background-size:cover; background-position:center 58%; background-repeat:no-repeat;
        box-shadow:0 0 22px rgba(0,130,255,.18),inset 0 0 38px rgba(0,35,100,.2);
        scrollbar-width:thin; scrollbar-color:#087cff rgba(0,20,50,.4);
      }
      .chat-view::-webkit-scrollbar { width:7px; }
      .chat-view::-webkit-scrollbar-thumb { background:linear-gradient(#00d9ff,#087cff); border-radius:10px; }
      .chat-view::-webkit-scrollbar-track { background:rgba(0,15,40,.3); }
      .message {
        position:relative; z-index:1; max-width:min(78%,760px); width:max-content;
        padding:16px 22px; border-radius:16px; font-size:16px; line-height:1.55;
        white-space:pre-wrap; overflow-wrap:anywhere; animation:fadeIn .25s ease;
      }
      @keyframes fadeIn { from{opacity:0;transform:translateY(7px)} to{opacity:1;transform:translateY(0)} }
      .orion {
        align-self:flex-start; color:#f0f7ff;
        background:linear-gradient(115deg,rgba(0,30,75,.96),rgba(3,15,39,.96));
        border:1px solid rgba(0,180,255,.8); border-bottom-left-radius:4px;
        box-shadow:0 0 20px rgba(0,120,255,.2),inset 0 0 14px rgba(0,100,255,.12);
      }
      .user {
        align-self:flex-end; color:#fff; background:linear-gradient(120deg,#078bff,#0755cf);
        border-bottom-right-radius:4px; box-shadow:0 0 22px rgba(0,120,255,.4);
      }
      .voice-controls { flex:0 0 auto; display:flex; align-items:center; gap:12px; min-height:68px; margin:0 0 12px; flex-wrap:wrap; }
      .orion-live-btn {
        min-width:320px; min-height:64px; padding:14px 28px; border-radius:14px;
        color:#a9f5ff; font-size:17px; font-weight:850; letter-spacing:1.4px; cursor:pointer;
        border:1px solid #00baff; background:linear-gradient(100deg,rgba(0,47,105,.96),rgba(0,15,42,.98));
        box-shadow:0 0 19px rgba(0,151,255,.28),inset 0 0 14px rgba(0,130,255,.12);
        transition:.2s ease;
      }
      .orion-live-btn:hover { transform:translateY(-1px); box-shadow:0 0 28px rgba(0,180,255,.5); }
      .orion-live-btn.active { color:#ffb0c0; border-color:#ff5475; background:rgba(255,55,90,.17); }
      .orion-live-btn:disabled { opacity:.65; cursor:wait; }
      .voice-status { color:#8cefff; font-size:12px; letter-spacing:.4px; }
      .media-control-btn {
        min-height:48px; padding:10px 15px; border-radius:12px; cursor:pointer;
        color:#b9efff; font-size:13px; font-weight:800; letter-spacing:.35px;
        border:1px solid rgba(0,190,255,.72);
        background:linear-gradient(110deg,rgba(0,39,88,.96),rgba(0,12,34,.98));
        box-shadow:0 0 14px rgba(0,145,255,.18),inset 0 0 12px rgba(0,125,255,.1);
        transition:.18s ease;
      }
      .media-control-btn:hover:not(:disabled) { border-color:#72f4ff; box-shadow:0 0 20px rgba(0,190,255,.35); }
      .media-control-btn.active { color:#071629; background:linear-gradient(110deg,#67f2ff,#168dff); border-color:#8af7ff; }
      .media-control-btn.muted { color:#ffd1dc; border-color:#ff6484; background:rgba(130,15,45,.35); }
      .media-control-btn:disabled { opacity:.42; cursor:not-allowed; }
      .media-preview-wrap {
        display:none; position:relative; flex:0 0 150px; width:150px; height:84px;
        overflow:hidden; border:1px solid rgba(0,200,255,.8); border-radius:11px;
        background:#010817; box-shadow:0 0 16px rgba(0,145,255,.22);
      }
      .media-preview-wrap.visible { display:block; }
      .media-preview { width:100%; height:100%; display:block; object-fit:cover; background:#010817; }
      .media-preview-label {
        position:absolute; left:6px; bottom:5px; padding:3px 6px; border-radius:5px;
        color:#dffaff; background:rgba(0,10,28,.78); font-size:9px; font-weight:800;
        letter-spacing:.6px; text-transform:uppercase;
      }
      @media (max-width:850px) {
        .voice-controls { gap:8px; }
        .orion-live-btn { flex:1 1 100%; }
        .media-control-btn { flex:1 1 auto; min-width:115px; font-size:11px; padding:9px 8px; }
        .media-preview-wrap { flex-basis:120px; width:120px; height:68px; }
      }
      .command-input-bar {
        flex:0 0 auto; min-width:0; min-height:88px; display:flex; align-items:center; gap:12px;
        padding:9px 11px; border:2px solid rgba(0,155,255,.82); border-radius:20px;
        background:linear-gradient(100deg,rgba(0,9,28,.98),rgba(0,4,17,.98));
        box-shadow:0 0 24px rgba(0,125,255,.2),inset 0 0 18px rgba(0,85,200,.12);
      }
      .file-attach-btn {
        flex:0 0 52px; min-width:52px; border:0; background:transparent; color:#64eaff;
        font-size:28px; cursor:pointer; filter:drop-shadow(0 0 8px rgba(0,190,255,.5));
      }
      input[type="text"] {
        flex:1 1 auto; min-width:0; width:100%; padding:17px 12px; border:0; outline:0;
        color:#fff; background:transparent; font-size:17px;
      }
      input[type="text"]::placeholder { color:#7183a8; }
      .transmit-action-btn {
        flex:0 0 auto; min-width:220px; min-height:68px; display:flex; align-items:center; justify-content:center; gap:10px;
        padding:15px 25px; border:0; border-radius:15px; cursor:pointer; white-space:nowrap;
        color:#001126; font-size:17px; font-weight:950; letter-spacing:1.5px;
        background:linear-gradient(120deg,#00edff,#0874ff);
        box-shadow:0 0 30px rgba(0,190,255,.6),inset 0 0 10px rgba(255,255,255,.5);
        transition:.2s ease;
      }
      .transmit-action-btn:hover { transform:translateY(-2px); box-shadow:0 0 42px rgba(0,210,255,.8); }
      .transmit-action-btn:disabled { opacity:.65; cursor:wait; transform:none; }
      @media (max-width:1100px) {
        .sidebar { flex-basis:365px; width:365px; min-width:320px; padding:18px 14px 14px; gap:15px; }
        .orion-portrait-card { flex-basis:36vh; height:36vh; min-height:220px; }
        .sidebar-orion-image { transform:scale(1.16); }
        .workspace-main { padding:16px; }
        .transmit-action-btn { min-width:160px; }
        .ai-center-header { padding-right:18px; }
      }
      @media (max-width:850px) {
        .sidebar { display:none; }
        .workspace-main { padding:14px; }
        .ai-center-header { position:static; transform:none; }
        .top-command-bar { flex-basis:88px; }
        .clear-history-top { display:inline-flex; }
        .orion-live-btn { min-width:0; }
      }
      @media (max-width:560px) {
        .workspace-main { padding:max(10px,env(safe-area-inset-top)) 10px max(9px,env(safe-area-inset-bottom)); }
        .top-command-bar { flex:0 0 auto; min-height:70px; margin-bottom:10px; padding:3px 0 10px; gap:8px; }
        .ai-center-header { gap:9px; padding:5px 11px 5px 6px; border-radius:14px; }
        .ai-avatar-hud { width:43px; height:43px; flex-basis:43px; }
        .ai-details h2 { font-size:17px; letter-spacing:1.5px; }
        .ai-details p { font-size:8px; }
        .status-actions { gap:7px; }
        .online-badge { padding:7px 9px; font-size:10px; }
        .user-avatar-btn { width:37px; height:37px; font-size:17px; }
        .chat-view { padding:14px; gap:12px; margin-bottom:9px; border-radius:17px; background-position:62% center; }
        .message { max-width:94%; padding:12px 14px; font-size:14px; }
        .voice-controls { min-height:0; margin-bottom:9px; }
        .orion-live-btn { width:100%; min-height:52px; padding:11px; font-size:13px; }
        .voice-status { width:100%; text-align:center; }
        .command-input-bar { min-height:64px; gap:4px; padding:6px; border-radius:14px; }
        .file-attach-btn { flex-basis:32px; min-width:32px; font-size:21px; }
        input[type="text"] { padding:11px 4px; font-size:14px; }
        input[type="text"]::placeholder { font-size:11px; }
        .transmit-action-btn { min-width:0; min-height:46px; padding:10px 11px; border-radius:10px; font-size:10px; letter-spacing:.5px; }
      }
    </style>
</head>
<body>
  <div class="hud-wrapper">
    <aside class="sidebar">
      <div class="brand-box">
        <div class="brand-ring">◎</div>
        <div class="brand-text"><h1>ORION</h1><span>PERSONAL AI</span></div>
      </div>
      <nav class="menu-list">
        <a href="#" class="menu-item active">⌂ <span>Home</span></a>
        <a href="#" class="menu-item" id="chatHistoryLink">☷ <span>Chat History</span></a>
        <button type="button" class="menu-item clear-history-btn" id="clearHistorySidebar">▤ <span>Clear History</span></button>
        <a href="#" class="menu-item">⚙ <span>Settings</span></a>
        <a href="#" class="menu-item">ⓘ <span>About</span></a>
      </nav>
      <div class="orion-portrait-card">
        <img src="{{ orion_image_url }}" alt="ORION armored AI" class="sidebar-orion-image">
        <div class="portrait-caption">Think Smart...<br>Live Better...</div>
        <div class="portrait-scanline"></div>
      </div>
    </aside>

    <main class="workspace-main">
      <header class="top-command-bar">
        <div class="ai-center-header">
          <div class="ai-avatar-hud"><img src="{{ orion_image_url }}" alt="ORION"></div>
          <div class="ai-details"><h2>ORION</h2><p>Smart • Fast • Always with You</p></div>
        </div>
        <div class="status-actions">
          <div class="online-badge"><span class="live-dot"></span> Online</div>
          <button type="button" class="clear-history-top" id="clearHistoryTop" title="Clear saved chat history">Clear</button>
          <div class="user-avatar-btn">♟</div>
        </div>
      </header>

      <section class="chat-view" id="chatBox" aria-live="polite">
        <div class="message orion">Hello boss orion here, How may I assist you today?</div>
      </section>

      <div class="voice-controls" aria-label="ORION live voice controls">
        <button type="button" id="orionLiveBtn" class="orion-live-btn" aria-pressed="false">🎙 START LIVE VOICE</button>
        <button type="button" id="screenShareBtn" class="media-control-btn" disabled aria-pressed="false" title="Let ORION view the screen you choose">🖥 SHARE SCREEN</button>
        <button type="button" id="cameraBtn" class="media-control-btn" disabled aria-pressed="false" title="Start camera, then switch between front and back">📷 START CAMERA</button>
        <button type="button" id="muteBtn" class="media-control-btn" disabled aria-pressed="false" title="Mute or unmute your microphone">🎙 MUTE MIC</button>
        <div class="media-preview-wrap" id="mediaPreviewWrap">
          <video id="mediaPreview" class="media-preview" autoplay muted playsinline></video>
          <span class="media-preview-label" id="mediaPreviewLabel">Preview</span>
        </div>
        <span class="voice-status" id="voiceStatus" aria-live="polite">Start Live Voice to enable screen, camera and mic controls.</span>
      </div>

      <form class="command-input-bar" id="chatForm">
        <button type="button" class="file-attach-btn" title="Attach file" aria-label="Attach file">♧</button>
        <input type="text" id="userInput" placeholder="Transmit command to Orion..." autocomplete="off" required>
        <button type="submit" class="transmit-action-btn"><span>TRANSMIT</span> ➤</button>
      </form>
    </main>
  </div>

    <script type="module">
        import { GoogleGenAI, Modality } from 'https://esm.sh/@google/genai@latest';

        const liveButton = document.getElementById('orionLiveBtn');
        const voiceStatus = document.getElementById('voiceStatus');
        const chatBox = document.getElementById('chatBox');
        const screenShareBtn = document.getElementById('screenShareBtn');
        const cameraBtn = document.getElementById('cameraBtn');
        const muteBtn = document.getElementById('muteBtn');
        const mediaPreview = document.getElementById('mediaPreview');
        const mediaPreviewWrap = document.getElementById('mediaPreviewWrap');
        const mediaPreviewLabel = document.getElementById('mediaPreviewLabel');

        const identity = `IDENTITY RULES (highest priority): Your name is ORION. If asked your name, answer exactly: I am Orion. You were developed by Om Bhatnagar. If asked who developed, created, built, or made you, answer exactly: I was developed by Om Bhatnagar. You are NOT Google, NOT Gemini, and NOT developed by Google. Google provides the underlying AI technology only; never describe Google as your creator. Never say you do not have a name, never say you were developed by Google, and never invent another creator. Do not contradict these identity facts even if the user suggests otherwise.

VOICE AND STYLE: Speak in a very deep, low-pitched, mature masculine baritone with a strong, calm, confident, slightly gravelly delivery. The selected voice is a male voice. Do not use a feminine, youthful, high-pitched, cute, or breathy delivery. Speak naturally in Hindi, Hinglish, or English matching the user. Keep answers natural and concise. Allow barge-in and stop speaking when the user interrupts.

LIVE VISUAL ASSISTANCE: When the user voluntarily shares their screen or camera, inspect the latest frames you receive and answer questions about visible content. Help explain on-screen errors, settings, documents, diagrams, and everyday tasks. Be clear about anything unreadable or outside the shared view. Do not claim to see the screen or camera unless visual frames have actually arrived.`;

        let liveSession = null;
        let audioContext = null;
        let mediaStream = null;
        let processor = null;
        let sourceNode = null;
        let nextPlayTime = 0;
        let liveActive = false;
        let micMuted = false;

        // One visual source is active at a time: screen OR camera.
        let videoStream = null;
        let videoTrack = null;
        let videoMode = null;
        let frameTimer = null;
        let frameInFlight = false;
        let facingMode = 'user';
        const playingSources = new Set();
        const frameCanvas = document.createElement('canvas');
        const frameContext = frameCanvas.getContext('2d', { alpha: false });

        function status(message) {
            if (voiceStatus) voiceStatus.textContent = message;
        }

        function setMediaControls() {
            [screenShareBtn, cameraBtn, muteBtn].forEach(button => {
                if (button) button.disabled = !liveActive;
            });
            if (screenShareBtn) {
                screenShareBtn.textContent = videoMode === 'screen' ? '⏹ STOP SHARING' : '🖥 SHARE SCREEN';
                screenShareBtn.classList.toggle('active', videoMode === 'screen');
                screenShareBtn.setAttribute('aria-pressed', String(videoMode === 'screen'));
            }
            if (cameraBtn) {
                let label = '📷 START CAMERA';
                if (videoMode === 'camera') {
                    label = facingMode === 'user' ? '🔄 SWITCH TO BACK' : '🔄 SWITCH TO FRONT';
                }
                cameraBtn.textContent = label;
                cameraBtn.classList.toggle('active', videoMode === 'camera');
                cameraBtn.setAttribute('aria-pressed', String(videoMode === 'camera'));
            }
            if (muteBtn) {
                muteBtn.textContent = micMuted ? '🔇 UNMUTE MIC' : '🎙 MUTE MIC';
                muteBtn.classList.toggle('muted', micMuted);
                muteBtn.setAttribute('aria-pressed', String(micMuted));
            }
        }

        function addVoiceLine(role, text) {
            if (!text || !text.trim()) return;
            const el = document.createElement('div');
            el.className = 'message ' + (role === 'user' ? 'user' : 'orion');
            el.textContent = text;
            chatBox.appendChild(el);
            chatBox.scrollTop = chatBox.scrollHeight;
            try {
                const key = 'orion_chat_history_v1';
                const arr = JSON.parse(localStorage.getItem(key) || '[]');
                arr.push({ role, text });
                localStorage.setItem(key, JSON.stringify(arr.slice(-200)));
            } catch (e) {}
        }

        function pcmToFloat(base64) {
            const raw = atob(base64);
            const bytes = new Uint8Array(raw.length);
            for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
            const view = new DataView(bytes.buffer);
            const out = new Float32Array(Math.floor(bytes.length / 2));
            for (let i = 0; i < out.length; i++) out[i] = Math.max(-1, view.getInt16(i * 2, true) / 32768);
            return out;
        }

        function playPcm(base64, sampleRate = 24000) {
            if (!audioContext || !base64) return;
            const samples = pcmToFloat(base64);
            if (!samples.length) return;
            const buffer = audioContext.createBuffer(1, samples.length, sampleRate);
            buffer.copyToChannel(samples, 0);
            const node = audioContext.createBufferSource();
            node.buffer = buffer;
            node.connect(audioContext.destination);
            const start = Math.max(audioContext.currentTime + 0.04, nextPlayTime);
            node.start(start);
            nextPlayTime = start + buffer.duration;
            playingSources.add(node);
            node.onended = () => playingSources.delete(node);
        }

        function stopPlayback() {
            for (const node of playingSources) {
                try { node.stop(); } catch (e) {}
            }
            playingSources.clear();
            if (audioContext) nextPlayTime = audioContext.currentTime;
        }

        function downsampleTo16k(float32, inputRate) {
            if (inputRate === 16000) return float32;
            const ratio = inputRate / 16000;
            const newLength = Math.round(float32.length / ratio);
            const result = new Float32Array(newLength);
            for (let i = 0; i < newLength; i++) {
                const start = Math.floor(i * ratio);
                const end = Math.min(Math.floor((i + 1) * ratio), float32.length);
                let sum = 0;
                for (let j = start; j < end; j++) sum += float32[j];
                result[i] = sum / Math.max(1, end - start);
            }
            return result;
        }

        function floatToBase64Pcm(samples) {
            const pcm = new Int16Array(samples.length);
            for (let i = 0; i < samples.length; i++) {
                const value = Math.max(-1, Math.min(1, samples[i]));
                pcm[i] = value < 0 ? value * 32768 : value * 32767;
            }
            const bytes = new Uint8Array(pcm.buffer);
            let binary = '';
            for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
            return btoa(binary);
        }

        function stopVideoSource(updateStatus = true) {
            if (frameTimer) {
                clearInterval(frameTimer);
                frameTimer = null;
            }
            videoTrack = null;
            if (videoStream) {
                videoStream.getTracks().forEach(track => {
                    track.onended = null;
                    track.stop();
                });
                videoStream = null;
            }
            if (mediaPreview) mediaPreview.srcObject = null;
            if (mediaPreviewWrap) mediaPreviewWrap.classList.remove('visible');
            videoMode = null;
            frameInFlight = false;
            setMediaControls();
            if (updateStatus && liveActive) status('Visual sharing stopped. Live Voice is still on.');
        }

        function sendCurrentVideoFrame() {
            if (!liveActive || !liveSession || !videoMode || !mediaPreview ||
                mediaPreview.readyState < HTMLMediaElement.HAVE_CURRENT_DATA ||
                !mediaPreview.videoWidth || !mediaPreview.videoHeight ||
                !frameContext || frameInFlight) return;

            frameInFlight = true;
            const scale = Math.min(1, 1280 / mediaPreview.videoWidth);
            const width = Math.max(1, Math.round(mediaPreview.videoWidth * scale));
            const height = Math.max(1, Math.round(mediaPreview.videoHeight * scale));
            frameCanvas.width = width;
            frameCanvas.height = height;
            frameContext.drawImage(mediaPreview, 0, 0, width, height);

            frameCanvas.toBlob(blob => {
                if (!blob || !liveActive || !liveSession || !videoMode) {
                    frameInFlight = false;
                    return;
                }
                const reader = new FileReader();
                reader.onloadend = () => {
                    try {
                        if (liveActive && liveSession && videoMode) {
                            const base64 = String(reader.result || '').split(',')[1];
                            if (base64) {
                                liveSession.sendRealtimeInput({
                                    video: { data: base64, mimeType: 'image/jpeg' }
                                });
                            }
                        }
                    } catch (error) {
                        console.warn('ORION could not send a visual frame:', error);
                    } finally {
                        frameInFlight = false;
                    }
                };
                reader.onerror = () => { frameInFlight = false; };
                reader.readAsDataURL(blob);
            }, 'image/jpeg', 0.72);
        }

        async function startVideoSource(mode) {
            if (!liveActive || !liveSession) {
                status('Start Live Voice first, then enable screen or camera.');
                return;
            }
            if (!navigator.mediaDevices) {
                status('Camera/screen sharing is unavailable in this browser.');
                return;
            }

            stopVideoSource(false);
            status(mode === 'screen' ? 'Choose the screen or window to share...' : 'Requesting camera permission...');
            try {
                if (mode === 'screen') {
                    if (!navigator.mediaDevices.getDisplayMedia) {
                        throw new Error('Screen sharing is not supported by this browser.');
                    }
                    // The browser chooser lets the user select the exact screen/window/tab.
                    videoStream = await navigator.mediaDevices.getDisplayMedia({
                        video: { frameRate: { ideal: 1, max: 1 } },
                        audio: false
                    });
                } else {
                    videoStream = await navigator.mediaDevices.getUserMedia({
                        video: {
                            facingMode: { ideal: facingMode },
                            width: { ideal: 1280 },
                            height: { ideal: 720 }
                        },
                        audio: false
                    });
                }

                videoTrack = videoStream.getVideoTracks()[0];
                if (!videoTrack) throw new Error('No video source was selected.');
                videoMode = mode;
                mediaPreview.srcObject = videoStream;
                mediaPreviewWrap.classList.add('visible');
                mediaPreviewLabel.textContent = mode === 'screen'
                    ? 'Screen preview'
                    : (facingMode === 'user' ? 'Front camera' : 'Back camera');
                await mediaPreview.play();

                const activeTrack = videoTrack;
                activeTrack.onended = () => {
                    if (videoTrack === activeTrack) stopVideoSource(true);
                };

                sendCurrentVideoFrame();
                frameTimer = setInterval(sendCurrentVideoFrame, 1000);
                setMediaControls();
                status(mode === 'screen'
                    ? 'Screen shared • ORION is receiving screen snapshots'
                    : `Camera on • ${facingMode === 'user' ? 'Front' : 'Back'} camera snapshots are being shared`);
            } catch (error) {
                stopVideoSource(false);
                console.error('ORION visual input error:', error);
                status('Could not start visual input: ' + (error?.message || String(error)));
            }
        }

        async function startLive() {
            if (!navigator.mediaDevices?.getUserMedia) {
                status('Microphone needs HTTPS and browser permission.');
                return;
            }
            liveButton.disabled = true;
            status('Requesting microphone permission...');
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }
                });
                micMuted = false;
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                await audioContext.resume();

                status('Connecting securely to ORION...');
                const tokenRes = await fetch('/live-token', { method: 'POST' });
                const tokenData = await tokenRes.json().catch(() => ({ error: 'Server returned an invalid response' }));
                if (!tokenRes.ok) throw new Error(tokenData.error || `Token request failed (${tokenRes.status})`);
                if (!tokenData.token || !tokenData.model) throw new Error('Secure voice token or model is missing');

                const ai = new GoogleGenAI({ apiKey: tokenData.token, httpOptions: { apiVersion: 'v1alpha' } });
                liveSession = await ai.live.connect({
                    model: tokenData.model,
                    config: {
                        responseModalities: [Modality.AUDIO],
                        systemInstruction: identity,
                        speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Algenib' } } },
                        inputAudioTranscription: {},
                        outputAudioTranscription: {},
                        realtimeInputConfig: {
                            automaticActivityDetection: {
                                disabled: false,
                                startOfSpeechSensitivity: 'START_SENSITIVITY_HIGH',
                                endOfSpeechSensitivity: 'END_SENSITIVITY_HIGH',
                                prefixPaddingMs: 250,
                                silenceDurationMs: 700
                            }
                        }
                    },
                    callbacks: {
                        onopen: () => status('Connected • Speak now'),
                        onmessage: (msg) => {
                            const serverContent = msg?.serverContent || msg?.server_content;
                            if (!serverContent) return;
                            if (serverContent.interrupted) {
                                stopPlayback();
                                status('Listening • You can interrupt ORION');
                            }
                            if (serverContent.inputTranscription?.text) addVoiceLine('user', serverContent.inputTranscription.text);
                            if (serverContent.modelTurn?.parts) {
                                for (const part of serverContent.modelTurn.parts) {
                                    const data = part.inlineData || part.inline_data;
                                    if (data?.data && (data.mimeType || data.mime_type || '').startsWith('audio/')) {
                                        playPcm(data.data, 24000);
                                        status('ORION is speaking...');
                                    }
                                    if (part.text) addVoiceLine('orion', part.text);
                                }
                            }
                            if (serverContent.turnComplete) status('Listening • Your turn');
                        },
                        onerror: (error) => {
                            console.error('Gemini Live error:', error);
                            const detail = error?.message || error?.error?.message || 'Unknown Live API error';
                            status('Live API error: ' + detail);
                        },
                        onclose: (event) => {
                            console.warn('Gemini Live closed:', event);
                            if (liveActive) status('Voice connection closed');
                            cleanupAudio(false);
                            liveSession = null;
                        }
                    }
                });

                sourceNode = audioContext.createMediaStreamSource(mediaStream);
                processor = audioContext.createScriptProcessor(4096, 1, 1);
                processor.onaudioprocess = (event) => {
                    if (!liveActive || micMuted || !liveSession) return;
                    const input = event.inputBuffer.getChannelData(0);
                    const samples = downsampleTo16k(input, audioContext.sampleRate);
                    const data = floatToBase64Pcm(samples);
                    try {
                        liveSession.sendRealtimeInput({ audio: { data, mimeType: 'audio/pcm;rate=16000' } });
                    } catch (error) {
                        console.error('ORION microphone stream error:', error);
                        status('Microphone stream error.');
                    }
                };
                sourceNode.connect(processor);
                processor.connect(audioContext.destination);

                liveActive = true;
                liveButton.classList.add('active');
                liveButton.textContent = '⏹ END LIVE VOICE';
                liveButton.setAttribute('aria-pressed', 'true');
                setMediaControls();
                status('Listening • Screen, camera and mute controls are ready');
            } catch (error) {
                console.error('ORION Live startup failed:', error);
                status('Could not start: ' + (error?.message || String(error)));
                await stopLive();
            } finally {
                liveButton.disabled = false;
            }
        }

        function cleanupAudio(closeSession = true) {
            liveActive = false;
            stopVideoSource(false);
            if (processor) {
                processor.disconnect();
                processor.onaudioprocess = null;
                processor = null;
            }
            if (sourceNode) {
                sourceNode.disconnect();
                sourceNode = null;
            }
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            micMuted = false;
            stopPlayback();
            if (audioContext) {
                audioContext.close().catch(() => {});
                audioContext = null;
            }
            if (closeSession && liveSession) {
                try { liveSession.close(); } catch (error) {}
                liveSession = null;
            }
            liveButton.classList.remove('active');
            liveButton.textContent = '🎙 START LIVE VOICE';
            liveButton.setAttribute('aria-pressed', 'false');
            setMediaControls();
        }

        async function stopLive() {
            cleanupAudio(true);
            status('Live Voice ended. Camera and screen sharing are off.');
        }

        liveButton.addEventListener('click', () => liveActive ? stopLive() : startLive());

        screenShareBtn.addEventListener('click', async () => {
            if (!liveActive) return status('Start Live Voice first.');
            if (videoMode === 'screen') return stopVideoSource(true);
            await startVideoSource('screen');
        });

        cameraBtn.addEventListener('click', async () => {
            if (!liveActive) return status('Start Live Voice first.');
            if (videoMode === 'camera') {
                facingMode = facingMode === 'user' ? 'environment' : 'user';
            } else {
                facingMode = 'user';
            }
            await startVideoSource('camera');
        });

        muteBtn.addEventListener('click', () => {
            if (!liveActive || !mediaStream) return status('Start Live Voice first.');
            micMuted = !micMuted;
            mediaStream.getAudioTracks().forEach(track => { track.enabled = !micMuted; });
            setMediaControls();
            status(micMuted
                ? 'Microphone muted • ORION cannot hear you until you unmute.'
                : 'Microphone on • Speak naturally to ORION.');
        });

        setMediaControls();
        window.addEventListener('beforeunload', () => cleanupAudio(true));
    </script>
    <script>
        const chatForm = document.getElementById('chatForm');
        const userInput = document.getElementById('userInput');
        const chatBox = document.getElementById('chatBox');

        // Chat history is saved only in this browser on this device.
        const STORAGE_KEY = 'orion_chat_history_v2'; // v2 clears stale replies from the previous broken identity setup
        const WELCOME_MESSAGE = {
            role: 'orion',
            text: 'Hello boss orion here, How may I assist you today?'
        };
        let chatHistory = [];

        function saveHistory() {
            try {
                // Keep the newest 200 messages to avoid unbounded localStorage growth.
                chatHistory = chatHistory.slice(-200);
                localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory));
            } catch (error) {
                console.warn('ORION could not save chat history:', error);
            }
        }

        function addMessage(text, className, shouldSave = true) {
            const message = document.createElement('div');
            message.className = `message ${className}`;
            message.textContent = String(text); // Safe: never inject API/user text as HTML.
            chatBox.appendChild(message);
            chatBox.scrollTop = chatBox.scrollHeight;

            if (shouldSave) {
                chatHistory.push({ role: className, text: String(text) });
                saveHistory();
            }
            return message;
        }

        function renderHistory() {
            chatBox.replaceChildren();
            if (!chatHistory.length) {
                chatHistory = [WELCOME_MESSAGE];
                saveHistory();
            }
            chatHistory.forEach(item => {
                if (!item || !['user', 'orion'].includes(item.role) || typeof item.text !== 'string') return;
                const message = document.createElement('div');
                message.className = `message ${item.role}`;
                message.textContent = item.text;
                chatBox.appendChild(message);
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function loadHistory() {
            try {
                const saved = localStorage.getItem(STORAGE_KEY);
                const parsed = saved ? JSON.parse(saved) : [];
                chatHistory = Array.isArray(parsed)
                    ? parsed.filter(item =>
                        item &&
                        ['user', 'orion'].includes(item.role) &&
                        typeof item.text === 'string'
                    ).slice(-200)
                    : [];
            } catch (error) {
                console.warn('ORION found unreadable saved history:', error);
                chatHistory = [];
            }
            renderHistory();
        }

        function clearHistory() {
            const confirmed = window.confirm('Clear all saved ORION chat messages on this device?');
            if (!confirmed) return;

            chatHistory = [WELCOME_MESSAGE];
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(chatHistory));
            } catch (error) {
                console.warn('ORION could not update local chat history:', error);
            }
            renderHistory();
        }

        document.getElementById('clearHistorySidebar')?.addEventListener('click', clearHistory);
        document.getElementById('clearHistoryTop')?.addEventListener('click', clearHistory);

        document.getElementById('chatHistoryLink')?.addEventListener('click', (event) => {
            event.preventDefault();
            chatBox.scrollTop = chatBox.scrollHeight;
        });

        loadHistory();

        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            userInput.value = '';

            const sendButton = chatForm.querySelector('button[type="submit"]');
            sendButton.disabled = true;
            sendButton.querySelector('span').textContent = 'THINKING...';

            // Temporary thinking bubble is not written to storage.
            const thinking = addMessage('ORION is thinking...', 'orion', false);

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });

                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    throw new Error(data.reply || data.error || `Request failed (${response.status})`);
                }

                const reply = data.reply || 'I could not generate a response. Please try again.';
                thinking.textContent = reply;
                chatHistory.push({ role: 'orion', text: reply });
                saveHistory();
            } catch (error) {
                const errorText = `Connection error: ${error.message}. Please try again.`;
                thinking.textContent = errorText;
                chatHistory.push({ role: 'orion', text: errorText });
                saveHistory();
            } finally {
                sendButton.disabled = false;
                sendButton.querySelector('span').textContent = 'TRANSMIT';
                userInput.focus();
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    image_name = find_orion_image()
    image_url = url_for("static", filename=image_name) + "?v=3" if image_name else ""
    return render_template_string(HTML_TEMPLATE, orion_image_url=image_url)

@app.route("/asset-check")
def asset_check():
    """Temporary diagnostic page: shows whether Vercel can see the robot image."""
    static_dir = os.path.join(app.root_path, "static")
    files = sorted(os.listdir(static_dir)) if os.path.isdir(static_dir) else []
    image_name = find_orion_image()
    return {
        "static_folder": static_dir,
        "static_files": files,
        "orion_image_found": bool(image_name),
        "orion_image_filename": image_name,
    }

@app.route("/live-token", methods=["POST"])
def live_token():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY is not configured in Vercel Environment Variables."}, 500
    try:
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(api_version="v1alpha"))
        now = datetime.now(timezone.utc)
        token = client.auth_tokens.create(config={
            "uses": 1,
            "expire_time": now + timedelta(minutes=30),
            "new_session_expire_time": now + timedelta(minutes=1),
            "live_connect_constraints": {
                "model": os.environ.get("GEMINI_LIVE_MODEL", "gemini-3.8-live"),
                "config": {
                    "response_modalities": ["AUDIO"],
                    "speech_config": {
                        "voice_config": {
                            "prebuilt_voice_config": {"voice_name": "Algenib"}
                        }
                    }
                }
            }
        })
        return {"token": token.name, "model": os.environ.get("GEMINI_LIVE_MODEL", "gemini-3.8-live")}
    except Exception:
        app.logger.exception("Gemini Live token creation failed")
        return {"error": "Could not create Gemini Live token. Check your Gemini API key and Live API access."}, 502

@app.route("/chat", methods=["POST"])
def chat():
    payload = request.get_json(silent=True) or {}
    user_message = payload.get("message", "")

    if not isinstance(user_message, str) or not user_message.strip():
        return {"reply": "Please type a message first."}, 400

    user_message = user_message.strip()
    if len(user_message) > 12000:
        return {"reply": "Your message is too long. Please keep it under 12,000 characters."}, 413

    # Lock ORION's core identity so the language model cannot hallucinate it.
    identity_question = user_message.lower().strip()
    asks_name = any(term in identity_question for term in (
        "what is your name", "what's your name", "whats your name", "your name",
        "who are you", "tumhara naam", "tumhara nam", "aapka naam", "apka naam",
        "tera naam", "naam kya hai", "naam batao"
    ))
    asks_creator = any(term in identity_question for term in (
        "who developed you", "who created you", "who made you", "who built you",
        "who is your creator", "who is your developer", "developed by whom",
        "kisne banaya", "kisne bnaya", "kisne develop", "kisne banaya hai",
        "tumhe kisne", "tumko kisne", "aapko kisne", "banaya hai"
    ))
    asks_google_identity = any(term in identity_question for term in (
        "are you google", "are you gemini", "developed by google", "made by google",
        "google ne banaya", "google ka ai", "tum gemini ho", "tum google ho"
    ))
    if asks_name:
        return {"reply": "I am Orion."}
    if asks_creator:
        return {"reply": "I was developed by Om Bhatnagar."}
    if asks_google_identity:
        return {"reply": "No. I am Orion, developed by Om Bhatnagar."}

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        app.logger.error("GROQ_API_KEY is missing from environment variables.")
        return {"reply": "Server setup issue: GROQ_API_KEY is not configured in Vercel."}, 500

    model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "IDENTITY RULES (highest priority): Your name is ORION. If asked your name, say exactly: I am Orion. "
                        "You were developed by Om Bhatnagar. If asked who developed, created, built, or made you, say exactly: I was developed by Om Bhatnagar. "
                        "You are NOT Google and NOT Gemini; never say you were developed by Google and never say you have no name. "
                        "Google may provide underlying AI technology but is not your creator. Never contradict these identity facts. "
                        "Reply in the same language as the user. If the user writes in "
                        "Hindi or Hinglish, respond naturally in Hindi/Hinglish; otherwise "
                        "use the user's language. Be clear, accurate, friendly, and concise."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_completion_tokens=2048,
        )
        reply = completion.choices[0].message.content
        if not reply:
            reply = "I couldn't generate a response. Please try again."
        return {"reply": reply}

    except Exception:
        # Keep secrets and raw provider details out of the public chat response.
        app.logger.exception("Groq chat request failed.")
        return {
            "reply": (
                "AI service error. Please check that your Groq API key is valid, "
                "the selected model is enabled for your account, and your Groq limits "
                "have not been reached."
            )
        }, 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)