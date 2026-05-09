from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import re
import random
from datetime import datetime
from collections import Counter
import unicodedata

app = FastAPI()

# Bangla Date System
BANGLA_NUMBERS = {0: '০', 1: '১', 2: '২', 3: '৩', 4: '৪', 5: '৫', 6: '৬', 7: '৭', 8: '৮', 9: '৯'}
BANGLA_DAYS = {'Monday': 'সোমবার', 'Tuesday': 'মঙ্গলবার', 'Wednesday': 'বুধবার', 'Thursday': 'বৃহস্পতিবার', 'Friday': 'শুক্রবার', 'Saturday': 'শনিবার', 'Sunday': 'রবিবার'}
BANGLA_MONTHS = ['বৈশাখ', 'জ্যৈষ্ঠ', 'আষাঢ়', 'শ্রাবণ', 'ভাদ্র', 'আশ্বিন', 'কার্তিক', 'অগ্রহায়ণ', 'পৌষ', 'মাঘ', 'ফাল্গুন', 'চৈত্র']

def to_bangla_number(num):
    return ''.join(BANGLA_NUMBERS[int(d)] for d in str(num))

def get_bangla_date():
    now = datetime.now()
    bangla_year = now.year - 593
    if now.month < 4:
        bangla_year -= 1
    month_index = (now.month - 1) % 12
    bangla_month = BANGLA_MONTHS[month_index]
    bangla_day = now.day if now.day > 13 else now.day + 17
    if bangla_day > 31:
        bangla_day = bangla_day - 31
    day_name = BANGLA_DAYS[now.strftime('%A')]
    time_12hr = now.strftime('%I:%M:%S %p')
    hour = now.hour
    if hour < 12:
        greeting = 'শুভ সকাল'
    elif hour < 18:
        greeting = 'শুভ বিকাল'
    else:
        greeting = 'শুভ রাত্রি'
    return {
        'short_date': f"{to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)}",
        'day_name': day_name,
        'time': time_12hr,
        'greeting': greeting
    }

# Helper Functions
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def extract_keywords(text, n=5):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    word_freq = Counter(words)
    stopwords = {'এবং', 'হয়ে', 'হতে', 'থেকে', 'একটি', 'এই', 'ও', 'সে', 'তা'}
    for stop in stopwords:
        word_freq.pop(stop, None)
    return [w for w, _ in word_freq.most_common(n)]

def summarize_text(text, ratio=0.3):
    sentences = re.split(r'[।?!]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    if len(sentences) <= 3:
        return text
    scored = []
    for sent in sentences:
        score = len(sent.split())
        score += len(extract_keywords(sent, 3)) * 2
        scored.append((sent, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    num = max(2, int(len(sentences) * ratio))
    selected = [s for s, _ in scored[:num]]
    selected.sort(key=lambda x: sentences.index(x))
    return '। '.join(selected) + '।'

def sentiment_analysis(text):
    positive = {'ভালো', 'চমৎকার', 'সুন্দর', 'আনন্দ', 'খুশি', 'পছন্দ', 'সফল'}
    negative = {'খারাপ', 'মন্দ', 'দুঃখ', 'বেদনা', 'ঘৃণা', 'ব্যর্থ', 'হার'}
    words = text.split()
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    if pos > neg:
        return 'পজিটিভ', '😊'
    elif neg > pos:
        return 'নেগেটিভ', '😢'
    return 'নিউট্রাল', '😐'

# API Models
class TextInput(BaseModel):
    text: str

# API Endpoints
@app.post("/api/summarizer")
async def summarizer(input_data: TextInput):
    text = clean_text(input_data.text)
    if len(text) < 20:
        return {"error": "কমপক্ষে ২০ অক্ষরের টেক্সট দিন"}
    summary = summarize_text(text)
    keywords = extract_keywords(text)
    return {
        "সারাংশ": summary,
        "মূল কীওয়ার্ড": ", ".join(keywords),
        "কম্প্রেশন": f"{(1 - len(summary)/len(text)) * 100:.1f}%"
    }

@app.post("/api/sentiment")
async def sentiment(input_data: TextInput):
    sentiment, emoji = sentiment_analysis(input_data.text)
    return {"সেন্টিমেন্ট": f"{sentiment} {emoji}"}

@app.post("/api/keywords")
async def keywords(input_data: TextInput):
    keywords = extract_keywords(input_data.text, 7)
    return {"কীওয়ার্ড": keywords}

# HTML Route
@app.get("/")
async def home():
    bangla_date = get_bangla_date()
    
    html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>বাংলা এআই স্যুট</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Hind Siliguri', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            min-height: 100vh;
        }}
        .header {{
            background: rgba(255,255,255,0.95);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .logo-icon {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .logo-icon i {{ font-size: 26px; color: white; }}
        .logo-text {{ font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; background-clip: text; color: transparent; }}
        .datetime-widget {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 8px 20px;
            border-radius: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
            color: white;
            font-size: 13px;
            flex-wrap: wrap;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .hero {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .hero h1 {{ font-size: 28px; color: #1e3c72; margin-bottom: 10px; }}
        .tools-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        .tool-card {{
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
            border: 2px solid transparent;
        }}
        .tool-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }}
        .tool-card.active {{ border-color: #667eea; background: linear-gradient(135deg, #fff, #f0f4ff); }}
        .tool-icon {{ font-size: 45px; margin-bottom: 10px; }}
        .tool-name {{ font-size: 16px; font-weight: 700; color: #1e3c72; }}
        .main-panel {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 25px;
        }}
        textarea {{
            width: 100%;
            min-height: 180px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
        }}
        textarea:focus {{ border-color: #667eea; outline: none; }}
        .btn-group {{ display: flex; gap: 12px; margin-top: 15px; flex-wrap: wrap; }}
        .btn {{
            padding: 10px 22px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            flex: 1;
        }}
        .btn-secondary {{ background: #f0f0f0; color: #333; }}
        .result-area {{
            margin-top: 20px;
            padding: 18px;
            background: #f9f9f9;
            border-radius: 12px;
            display: none;
        }}
        .result-box {{
            background: white;
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }}
        .loader {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
        .footer {{ text-align: center; padding: 20px; color: rgba(255,255,255,0.7); font-size: 12px; }}
        @media (max-width: 768px) {{
            .header {{ flex-direction: column; text-align: center; }}
            .tools-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon"><i class="fas fa-brain"></i></div>
            <span class="logo-text">বাংলা এআই স্যুট</span>
        </div>
        <div class="datetime-widget">
            <span>{bangla_date['greeting']}</span>
            <span>{bangla_date['day_name']}</span>
            <span>{bangla_date['short_date']}</span>
            <span>{bangla_date['time']}</span>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1><i class="fas fa-robot"></i> বাংলা এআই অল-ইন-ওয়ান স্যুট</h1>
            <p>টেক্সট সামারাইজ, সেন্টিমেন্ট অ্যানালাইসিস, কীওয়ার্ড এক্সট্র্যাকশন - সম্পূর্ণ বিনামূল্যে!</p>
        </div>

        <div class="tools-grid" id="tools-grid"></div>

        <div class="main-panel">
            <textarea id="input-text" placeholder="এখানে আপনার বাংলা টেক্সট লিখুন..."></textarea>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="processText()"><i class="fas fa-play"></i> প্রসেস করুন</button>
                <button class="btn btn-secondary" onclick="clearText()"><i class="fas fa-trash"></i> ক্লিয়ার</button>
                <button class="btn btn-secondary" onclick="loadExample()"><i class="fas fa-file-alt"></i> উদাহরণ</button>
            </div>
            <div id="result-area" class="result-area">
                <div id="result-content"></div>
            </div>
        </div>
        <div class="footer">
            <p><i class="fas fa-heart"></i> বাংলায় এআই - সম্পূর্ণ ফ্রি</p>
        </div>
    </div>

    <script>
        const tools = [
            {{ id: 'summarizer', icon: '📝', name: 'টেক্সট সামারাইজার' }},
            {{ id: 'sentiment', icon: '😊', name: 'সেন্টিমেন্ট অ্যানালাইসিস' }},
            {{ id: 'keywords', icon: '🔑', name: 'কীওয়ার্ড এক্সট্র্যাক্টর' }}
        ];
        let currentTool = tools[0];

        function renderTools() {{
            const grid = document.getElementById('tools-grid');
            grid.innerHTML = tools.map(tool => `
                <div class="tool-card ${{tool.id === currentTool.id ? 'active' : ''}}" onclick="selectTool('${{tool.id}}')">
                    <div class="tool-icon">${{tool.icon}}</div>
                    <div class="tool-name">${{tool.name}}</div>
                </div>
            `).join('');
        }}

        function selectTool(toolId) {{
            currentTool = tools.find(t => t.id === toolId);
            renderTools();
            document.getElementById('result-area').style.display = 'none';
        }}

        async function processText() {{
            const text = document.getElementById('input-text').value;
            if (!text.trim()) {{
                alert('দয়া করে কিছু টেক্সট লিখুন');
                return;
            }}
            
            const resultArea = document.getElementById('result-area');
            const resultContent = document.getElementById('result-content');
            resultArea.style.display = 'block';
            resultContent.innerHTML = '<div class="loader"></div> প্রসেসিং হচ্ছে...';
            
            try {{
                const response = await fetch(`/api/${{currentTool.id}}`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ text: text }})
                }});
                const data = await response.json();
                let html = '';
                for (let [key, value] of Object.entries(data)) {{
                    html += `<div class="result-box"><strong>📌 ${{key}}:</strong><br>${{value}}</div>`;
                }}
                resultContent.innerHTML = html;
            }} catch (error) {{
                resultContent.innerHTML = `<div class="result-box" style="background:#f8d7da;">❌ ${{error.message}}</div>`;
            }}
        }}

        function clearText() {{
            document.getElementById('input-text').value = '';
            document.getElementById('result-area').style.display = 'none';
        }}

        function loadExample() {{
            document.getElementById('input-text').value = 'বাংলাদেশ একটি ছোট কিন্তু জনবহুল দেশ। এটি দক্ষিণ এশিয়ায় অবস্থিত। ঢাকা এর রাজধানী। এখানে অনেক প্রাকৃতিক সৌন্দর্য রয়েছে। সুন্দরবন বিশ্বের সবচেয়ে বড় ম্যানগ্রোভ বন।';
        }}

        renderTools();
        selectTool('summarizer');
        loadExample();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

# Vercel handler
handler = app