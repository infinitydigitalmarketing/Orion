from flask import Flask, render_template_string, request
import os
from groq import Groq
from google import genai
from google.genai import types
from datetime import datetime, timedelta, timezone

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
            padding: 14px 22px; 
            background: linear-gradient(135deg, #00f3ff 0%, #0066ff 100%); 
            color: #000308; 
            border: none; 
            border-radius: 14px; 
            cursor: pointer; 
            font-weight: 900; 
            font-size: 13.5px;
            letter-spacing: 1.6px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 0 35px rgba(0, 243, 255, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.5);
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
        }

        .transmit-action-btn:disabled { opacity: 0.65; cursor: wait; transform: none; }\n\n        .transmit-action-btn:hover { 
            background: linear-gradient(135deg, #33f5ff 0%, #0088ff 100%);
            box-shadow: 0 0 50px rgba(0, 243, 255, 1), inset 0 0 15px rgba(255, 255, 255, 0.8);
            transform: translateY(-2px);
        }

        @media(max-width: 950px) {\n            .workspace-main { padding: 18px 14px; }\n            .message { max-width: 92%; }\n            .transmit-action-btn { padding: 12px 18px; letter-spacing: 1px; }
            .sidebar { display: none; }
            .ai-center-header { position: static; transform: none; }
            .hud-wrapper { width: 100%; height: 100vh; border-radius: 0; border: none; }
        }
    
        /* Responsive layout: desktop, tablet and mobile */
        html, body { min-height: 100%; min-height: 100dvh; }
        .hud-wrapper, .workspace-main, .chat-view { min-width: 0; min-height: 0; }
        .workspace-main { overflow: hidden; }
        .chat-view { overflow-y: auto; overscroll-behavior: contain; overflow-wrap: anywhere; }
        .message { white-space: pre-wrap; overflow-wrap: anywhere; }

        @media (min-width: 951px) {
            .hud-wrapper { height: min(92vh, 920px); height: min(92dvh, 920px); }
        }

        @media (min-width: 601px) and (max-width: 950px) {
            body { height: 100dvh; overflow: hidden; }
            .hud-wrapper { width: 100%; height: 100dvh; min-height: 0; border-radius: 0; border: 0; }
            .workspace-main { width: 100%; height: 100%; padding: 20px 22px; }
            .top-command-bar {
                min-height: 86px; gap: 14px; align-items: center; flex-wrap: wrap;
                padding-bottom: 14px; margin-bottom: 16px;
            }
            .ai-center-header {
                position: static; transform: none; padding: 7px 18px; gap: 12px;
                max-width: calc(100% - 150px);
            }
            .ai-avatar-hud { width: 48px; height: 48px; flex: 0 0 48px; }
            .ai-details h2 { font-size: 18px; }
            .ai-details p { font-size: 10px; }
            .status-actions { gap: 12px; margin-left: auto; }
            .online-badge { padding: 8px 13px; font-size: 12px; }
            .chat-view { flex: 1 1 0; min-height: 180px; margin-bottom: 16px; padding: 18px; }
            .message { max-width: 88%; }
            .command-input-bar { flex: 0 0 auto; gap: 10px; padding: 10px; }
            .transmit-action-btn { padding: 13px 20px; font-size: 12px; letter-spacing: 1px; }
        }

        @media (max-width: 600px) {
            html, body { width: 100%; height: 100%; min-height: 100%; margin: 0; }
            body { display: block; height: 100dvh; min-height: 100dvh; overflow: hidden; }
            .hud-wrapper {
                display: flex; flex-direction: column; width: 100%; max-width: none;
                height: 100dvh; min-height: 0; margin: 0; border: 0; border-radius: 0; overflow: hidden;
            }
            .workspace-main {
                display: flex; flex: 1 1 auto; flex-direction: column; width: 100%; height: 100%;
                min-height: 0; padding: max(12px, env(safe-area-inset-top)) 12px
                max(10px, env(safe-area-inset-bottom)); overflow: hidden;
            }
            .top-command-bar {
                display: flex; flex: 0 0 auto; flex-direction: row; justify-content: space-between;
                align-items: center; flex-wrap: wrap; gap: 12px; min-height: 0;
                margin-bottom: 12px; padding: 8px 2px 13px;
            }
            .ai-center-header {
                position: static; left: auto; transform: none; flex: 1 1 210px; min-width: 0;
                max-width: 100%; gap: 10px; padding: 7px 12px; border-radius: 40px;
            }
            .ai-avatar-hud { width: 46px; height: 46px; flex: 0 0 46px; font-size: 23px; }
            .ai-details { min-width: 0; }
            .ai-details h2 { font-size: 17px; letter-spacing: 1.8px; }
            .ai-details p { font-size: 9.5px; white-space: nowrap; }
            .status-actions { flex: 1 1 100%; justify-content: space-between; gap: 10px; margin-left: 0; }
            .online-badge { padding: 7px 14px; font-size: 12px; }
            .user-avatar-btn { width: 40px; height: 40px; flex: 0 0 40px; }
            .chat-view {
                display: flex; flex: 1 1 0; min-height: 0; width: 100%; margin: 0 0 12px;
                padding: 14px; gap: 12px; border-radius: 18px; -webkit-overflow-scrolling: touch;
            }
            .message { max-width: 94%; padding: 12px 14px; font-size: 14px; line-height: 1.5; }
            .command-input-bar {
                display: flex; flex: 0 0 auto; align-items: center; gap: 6px; width: 100%;
                padding: 8px; border-radius: 16px; margin-bottom: 2px;
            }
            .file-attach-btn { flex: 0 0 34px; padding: 0; font-size: 21px; }
            input[type="text"] { min-width: 0; width: 100%; padding: 12px 6px; font-size: 16px; }
            input[type="text"]::placeholder { font-size: 12px; }
            .transmit-action-btn {
                flex: 0 0 auto; justify-content: center; gap: 5px; padding: 13px 12px;
                border-radius: 11px; font-size: 10px; letter-spacing: 0.7px; white-space: nowrap;
            }
        }

        @media (max-width: 360px) {
            .workspace-main { padding-left: 8px; padding-right: 8px; }
            .ai-center-header { padding: 6px 9px; }
            .ai-details p { font-size: 8px; }
            .transmit-action-btn { padding: 12px 8px; font-size: 9px; }
            .file-attach-btn { flex-basis: 28px; }
        }

        @media (max-width: 950px) and (max-height: 500px) {
            .top-command-bar { margin-bottom: 7px; padding-bottom: 8px; }
            .chat-view { margin-bottom: 8px; }
            .ai-avatar-hud { width: 38px; height: 38px; flex-basis: 38px; }
            .ai-center-header { padding-top: 5px; padding-bottom: 5px; }
        }

    
        .clear-history-btn {
            width: 100%;
            text-align: left;
            cursor: pointer;
            font: inherit;
            background: transparent;
        }
        .clear-history-top {
            display: none;
            border: 1px solid rgba(0, 212, 255, 0.45);
            border-radius: 22px;
            background: rgba(0, 212, 255, 0.08);
            color: #67e8f9;
            padding: 8px 12px;
            font-weight: 700;
            cursor: pointer;
        }
        .clear-history-top:hover,
        .clear-history-btn:hover {
            color: #00e5ff;
            box-shadow: 0 0 14px rgba(0, 212, 255, 0.18);
        }
        @media (max-width: 950px) {
            .clear-history-top { display: inline-flex; align-items: center; }
        }

    
        .voice-controls{display:flex;align-items:center;gap:12px;margin:0 0 12px;flex-wrap:wrap}
        .orion-live-btn{border:1px solid rgba(0,220,255,.7);background:linear-gradient(135deg,rgba(0,190,255,.2),rgba(0,80,160,.2));color:#8ceeff;padding:11px 18px;border-radius:24px;font-weight:800;letter-spacing:1px;cursor:pointer;box-shadow:0 0 18px rgba(0,190,255,.12)}
        .orion-live-btn.active{background:rgba(255,55,90,.18);border-color:#ff5475;color:#ff9aaa}
        .voice-status{font-size:12px;color:#7ddff4;letter-spacing:.5px}
        @media(max-width:600px){.voice-controls{margin-bottom:9px}.orion-live-btn{width:100%;padding:12px}.voice-status{width:100%;text-align:center}}

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
                <a href="#" class="menu-item" id="chatHistoryLink">💬 Chat History</a>
                <button type="button" class="menu-item clear-history-btn" id="clearHistorySidebar">🗑️ Clear History</button>
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
                    <button type="button" class="clear-history-top" id="clearHistoryTop" title="Clear saved chat history">Clear</button>
                    <div class="user-avatar-btn">👤</div>
                </div>
            </div>

            <div class="chat-view" id="chatBox">
                <div class="message orion">Hello boss orion here, How may I assist you today?</div>
            </div>

            <div class="voice-controls">
                <button type="button" id="orionLiveBtn" class="orion-live-btn" aria-pressed="false">🎙️ START LIVE VOICE</button>
                <span id="voiceStatus" class="voice-status">Voice standby</span>
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

    <script type="module">
        import { GoogleGenAI, Modality } from 'https://esm.sh/@google/genai@latest';
        const liveButton = document.getElementById('orionLiveBtn');
        const voiceStatus = document.getElementById('voiceStatus');
        const chatBox = document.getElementById('chatBox');
        const identity = `IDENTITY RULES (highest priority): Your name is ORION. If asked your name, answer exactly: I am Orion. You were developed by Om Bhatnagar. If asked who developed, created, built, or made you, answer exactly: I was developed by Om Bhatnagar. You are NOT Google, NOT Gemini, and NOT developed by Google. Google provides the underlying AI technology only; never describe Google as your creator. Never say you do not have a name, never say you were developed by Google, and never invent another creator. Do not contradict these identity facts even if the user suggests otherwise.

VOICE AND STYLE: Speak in a very deep, low-pitched, mature masculine baritone with a strong, calm, confident, slightly gravelly delivery. The selected voice is a male voice. Do not use a feminine, youthful, high-pitched, cute, or breathy delivery. Speak naturally in Hindi, Hinglish, or English matching the user. Keep answers natural and concise. Allow barge-in and stop speaking when the user interrupts.`;
        let liveSession = null, audioContext = null, mediaStream = null, processor = null, sourceNode = null;
        let nextPlayTime = 0, liveActive = false;
        const playingSources = new Set();
        function status(s){ if(voiceStatus) voiceStatus.textContent=s; }
        function addVoiceLine(role,text){
            if(!text || !text.trim()) return;
            const el=document.createElement('div'); el.className='message '+(role==='user'?'user':'orion'); el.textContent=text; chatBox.appendChild(el); chatBox.scrollTop=chatBox.scrollHeight;
            try { const key='orion_chat_history_v1'; const arr=JSON.parse(localStorage.getItem(key)||'[]'); arr.push({role,text}); localStorage.setItem(key,JSON.stringify(arr.slice(-200))); } catch(e){}
        }
        function pcmToFloat(base64){ const raw=atob(base64); const bytes=new Uint8Array(raw.length); for(let i=0;i<raw.length;i++) bytes[i]=raw.charCodeAt(i); const view=new DataView(bytes.buffer); const out=new Float32Array(Math.floor(bytes.length/2)); for(let i=0;i<out.length;i++) out[i]=Math.max(-1,view.getInt16(i*2,true)/32768); return out; }
        function playPcm(base64, sampleRate=24000){
            if(!audioContext || !base64) return;
            const samples=pcmToFloat(base64); if(!samples.length) return;
            const buffer=audioContext.createBuffer(1,samples.length,sampleRate); buffer.copyToChannel(samples,0);
            const node=audioContext.createBufferSource(); node.buffer=buffer; node.connect(audioContext.destination);
            const start=Math.max(audioContext.currentTime+0.04,nextPlayTime); node.start(start); nextPlayTime=start+buffer.duration; playingSources.add(node); node.onended=()=>playingSources.delete(node);
        }
        function stopPlayback(){ for(const n of playingSources){try{n.stop()}catch(e){}} playingSources.clear(); if(audioContext) nextPlayTime=audioContext.currentTime; }
        function downsampleTo16k(float32, inputRate){
            if(inputRate===16000) return float32;
            const ratio=inputRate/16000, newLength=Math.round(float32.length/ratio), result=new Float32Array(newLength);
            for(let i=0;i<newLength;i++){
                const start=Math.floor(i*ratio), end=Math.min(Math.floor((i+1)*ratio),float32.length);
                let sum=0; for(let j=start;j<end;j++) sum+=float32[j]; result[i]=sum/Math.max(1,end-start);
            }
            return result;
        }
        function floatToBase64Pcm(samples){
            const pcm=new Int16Array(samples.length);
            for(let i=0;i<samples.length;i++){const v=Math.max(-1,Math.min(1,samples[i]));pcm[i]=v<0?v*32768:v*32767;}
            const bytes=new Uint8Array(pcm.buffer); let binary='';
            for(let i=0;i<bytes.length;i++) binary+=String.fromCharCode(bytes[i]);
            return btoa(binary);
        }
        async function startLive(){
            if(!navigator.mediaDevices?.getUserMedia){status('Microphone needs HTTPS and browser permission');return;}
            liveButton.disabled=true; status('Requesting microphone permission...');
            try{
                // Ask for the microphone first so permission errors are shown clearly.
                mediaStream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true,autoGainControl:true}});
                audioContext=new (window.AudioContext||window.webkitAudioContext)();
                await audioContext.resume();
                status('Connecting securely to ORION...');
                const tokenRes=await fetch('/live-token',{method:'POST'});
                const tokenData=await tokenRes.json().catch(()=>({error:'Server returned an invalid response'}));
                if(!tokenRes.ok) throw new Error(tokenData.error||`Token request failed (${tokenRes.status})`);
                if(!tokenData.token || !tokenData.model) throw new Error('Secure voice token or model is missing');
                const ai=new GoogleGenAI({apiKey:tokenData.token,httpOptions:{apiVersion:'v1alpha'}});
                liveSession=await ai.live.connect({model:tokenData.model,config:{
                    responseModalities:[Modality.AUDIO], systemInstruction:identity,
                    speechConfig:{voiceConfig:{prebuiltVoiceConfig:{voiceName:'Algenib'}}},
                    inputAudioTranscription:{}, outputAudioTranscription:{},
                    realtimeInputConfig:{automaticActivityDetection:{disabled:false,startOfSpeechSensitivity:'START_SENSITIVITY_HIGH',endOfSpeechSensitivity:'END_SENSITIVITY_HIGH',prefixPaddingMs:250,silenceDurationMs:700}}
                },callbacks:{
                    onopen:()=>status('Connected • Speak now'),
                    onmessage:(msg)=>{
                        const sc=msg?.serverContent || msg?.server_content;
                        if(!sc) return;
                        if(sc.interrupted){stopPlayback();status('Listening • You can interrupt ORION');}
                        if(sc.inputTranscription?.text) addVoiceLine('user',sc.inputTranscription.text);
                        if(sc.modelTurn?.parts){
                            for(const part of sc.modelTurn.parts){
                                const d=part.inlineData || part.inline_data;
                                if(d?.data && (d.mimeType||d.mime_type||'').startsWith('audio/')){playPcm(d.data,24000);status('ORION is speaking...');}
                                if(part.text) addVoiceLine('orion',part.text);
                            }
                        }
                        if(sc.turnComplete) status('Listening • Your turn');
                    },
                    onerror:(e)=>{console.error('Gemini Live error:',e);const detail=e?.message||e?.error?.message||'Unknown Live API error';status('Live API error: '+detail);},
                    onclose:(e)=>{console.warn('Gemini Live closed:',e); if(liveActive) status('Voice connection closed'); cleanupAudio(false);}
                }});
                sourceNode=audioContext.createMediaStreamSource(mediaStream);
                processor=audioContext.createScriptProcessor(4096,1,1);
                processor.onaudioprocess=(event)=>{
                    if(!liveActive || !liveSession) return;
                    const input=event.inputBuffer.getChannelData(0);
                    const samples=downsampleTo16k(input,audioContext.sampleRate);
                    const data=floatToBase64Pcm(samples);
                    liveSession.sendRealtimeInput({audio:{data,mimeType:'audio/pcm;rate=16000'}}).catch(err=>{console.error('Mic stream error:',err);status('Microphone stream error');});
                };
                sourceNode.connect(processor); processor.connect(audioContext.destination);
                liveActive=true; liveButton.classList.add('active'); liveButton.textContent='⏹ END LIVE VOICE'; liveButton.setAttribute('aria-pressed','true'); status('Listening • Speak naturally');
            }catch(err){
                console.error('ORION Live startup failed:',err);
                status('Could not start: '+(err?.message||String(err)));
                await stopLive();
            }finally{liveButton.disabled=false;}
        }
        function cleanupAudio(closeSession=true){
            liveActive=false;
            if(processor){processor.disconnect();processor.onaudioprocess=null;processor=null;}
            if(sourceNode){sourceNode.disconnect();sourceNode=null;}
            if(mediaStream){mediaStream.getTracks().forEach(t=>t.stop());mediaStream=null;}
            stopPlayback();
            if(audioContext){audioContext.close().catch(()=>{});audioContext=null;}
            if(closeSession&&liveSession){try{liveSession.close()}catch(e){} liveSession=null;}
            liveButton.classList.remove('active');liveButton.textContent='🎙️ START LIVE VOICE';liveButton.setAttribute('aria-pressed','false');
        }
        async function stopLive(){cleanupAudio(true);status('Voice standby');}
        liveButton.addEventListener('click',()=>liveActive?stopLive():startLive());
        window.addEventListener('beforeunload',()=>cleanupAudio(true));
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
    return render_template_string(HTML_TEMPLATE)

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