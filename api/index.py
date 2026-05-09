from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import re
import random
from datetime import datetime
from collections import Counter
import unicodedata

app = FastAPI()

# ==================== BANGLA DATE FUNCTIONS ====================

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
        'greeting': greeting,
        'full_datetime': f"{day_name}, {to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)} - {time_12hr}"
    }

# ==================== HELPER FUNCTIONS ====================

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def extract_keywords(text, n=5):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    word_freq = Counter(words)
    stopwords = {'এবং', 'হয়ে', 'হতে', 'থেকে', 'একটি', 'এই', 'ও', 'সে', 'তা', 'আমি', 'তুমি', 'করে', 'করা', 'হয়', 'ছিল', 'হবে'}
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
    positive = {'ভালো', 'চমৎকার', 'সুন্দর', 'আনন্দ', 'খুশি', 'পছন্দ', 'সফল', 'জয়', 'প্রিয়', 'দারুণ', 'অসাধারণ'}
    negative = {'খারাপ', 'মন্দ', 'দুঃখ', 'বেদনা', 'ঘৃণা', 'ব্যর্থ', 'হার', 'শোক', 'ক্ষতি', 'সমস্যা', 'ত্রুটি'}
    words = text.split()
    pos = sum(1 for w in words if w in positive)
    neg = sum(1 for w in words if w in negative)
    if pos > neg:
        return 'পজিটিভ', '😊', pos, neg
    elif neg > pos:
        return 'নেগেটিভ', '😢', pos, neg
    return 'নিউট্রাল', '😐', pos, neg

# ==================== API MODELS ====================

class TextInput(BaseModel):
    text: str

class EmailInput(BaseModel):
    email_content: str
    tone: str = "professional"

class ResumeInput(BaseModel):
    name: str
    email: str
    skills: str
    experience: str
    education: str

class InterviewAnswer(BaseModel):
    question: str
    answer: str

# ==================== API ENDPOINTS ====================

@app.get("/api/bangla-date")
async def bangla_date_api():
    return get_bangla_date()

# Tool 1: Text Summarizer
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
        "কম্প্রেশন রেট": f"{(1 - len(summary)/len(text)) * 100:.1f}%",
        "মূল টেক্সটের দৈর্ঘ্য": f"{len(text)} অক্ষর",
        "সারাংশের দৈর্ঘ্য": f"{len(summary)} অক্ষর"
    }

# Tool 2: Sentiment Analysis
@app.post("/api/sentiment")
async def sentiment(input_data: TextInput):
    sentiment, emoji, pos, neg = sentiment_analysis(input_data.text)
    return {
        "সেন্টিমেন্ট": f"{sentiment} {emoji}",
        "পজিটিভ স্কোর": pos,
        "নেগেটিভ স্কোর": neg
    }

# Tool 3: Keyword Extractor
@app.post("/api/keywords")
async def keywords(input_data: TextInput):
    keywords = extract_keywords(input_data.text, 7)
    return {"কীওয়ার্ড": keywords}

# Tool 4: Content Writer
@app.post("/api/content-writer")
async def content_writer(input_data: TextInput):
    topic = input_data.text
    blog_post = f"""## {topic}: একটি বিস্তারিত আলোচনা

### ভূমিকা
বর্তমান যুগে {topic} একটি অত্যন্ত গুরুত্বপূর্ণ বিষয়।

### {topic} এর গুরুত্ব
{topic} এর গুরুত্ব অপরিসীম। নিম্নলিখিত ক্ষেত্রে এটি বিশেষ ভূমিকা রাখে:
1. দক্ষতা বৃদ্ধি
2. সময় সাশ্রয়
3. নির্ভুলতা

### উপসংহার
{topic} আমাদের জীবনের একটি অপরিহার্য অংশ।"""
    return {"ব্লগ পোস্ট": blog_post, "হ্যাশট্যাগ": f"#{topic.replace(' ', '')} #বাংলা #টেকনোলজি"}

# Tool 5: Email Response
@app.post("/api/email-response")
async def email_response(input_data: EmailInput):
    if input_data.tone == "professional":
        response = f"""বিষয়: আপনার ইমেইলের জবাব

প্রিয় গ্রাহক,

আপনার ইমেইলটি পেয়ে ধন্যবাদ। খুব শীঘ্রই আপনার সাথে যোগাযোগ করব।

ধন্যবাদান্তে,
Bangla AI টিম"""
    else:
        response = f"""হ্যালো! 👋

আপনার মেইল পেয়েছি। খুব শীঘ্রই রিপ্লাই দিচ্ছি।

- Bangla AI টিম"""
    return {"জেনারেটেড রেসপন্স": response}

# Tool 6: Research Analyzer
@app.post("/api/research-analyzer")
async def research_analyzer(input_data: TextInput):
    paper = clean_text(input_data.text)
    sentences = re.split(r'[।?!]', paper)
    key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
    return {"মূল পয়েন্টসমূহ": key_points, "সাইটেশন": f"(লেখক, {datetime.now().year})"}

# Tool 7: Code Documentation
@app.post("/api/code-documentation")
async def code_documentation(input_data: TextInput):
    code = input_data.text
    if 'def ' in code:
        lang = "পাইথন"
        func_name = code.split('def ')[1].split('(')[0]
        doc = f'"""\n{func_name} ফাংশনের ডকুমেন্টেশন\n\nএই ফাংশনটি {func_name} এর কাজ সম্পাদন করে।\n"""'
    else:
        lang = "অজানা"
        doc = f"/*\nকোড ডকুমেন্টেশন\n\nএই কোডটি {code[:50]}...\n*/"
    return {"কোডের ভাষা": lang, "ডকুমেন্টেশন": doc}

# Tool 8: Social Media Content
@app.post("/api/social-content")
async def social_content(input_data: TextInput):
    topic = input_data.text
    post = f"""🚀 {topic} নিয়ে আমার চিন্তাভাবনা

{topic} বর্তমানে আলোচনার কেন্দ্রবিন্দুতে।

#BanglaAI #{topic.replace(' ', '')}"""
    return {"লিংকডইন পোস্ট": post, "হ্যাশট্যাগ": f"#{topic.replace(' ', '')} #BanglaAI"}

# Tool 9: Meeting Summarizer
@app.post("/api/meeting-summarizer")
async def meeting_summarizer(input_data: TextInput):
    notes = clean_text(input_data.text)
    sentences = notes.split('।')
    action_items = [s.strip() for s in sentences if 'করতে হবে' in s or 'প্রয়োজন' in s][:2]
    summary = summarize_text(notes)
    return {"মিটিং সারাংশ": summary, "অ্যাকশন আইটেম": action_items if action_items else ["কোন অ্যাকশন আইটেম নেই"]}

# Tool 10: Resume Parser
@app.post("/api/resume-parser")
async def resume_parser(input_data: ResumeInput):
    skills_list = [s.strip() for s in input_data.skills.split(',')]
    job_match = random.randint(65, 95)
    return {
        "নাম": input_data.name,
        "ইমেইল": input_data.email,
        "দক্ষতা": skills_list,
        "এটিএস স্কোর": f"{job_match}%"
    }

# Tool 11: Interview Preparation
@app.post("/api/interview-prep")
async def interview_prep(input_data: InterviewAnswer):
    word_count = len(input_data.answer.split())
    if word_count < 20:
        score, feedback, level = 40, "আরও বিস্তারিত উত্তর দিন", "উন্নতি প্রয়োজন"
    elif word_count < 50:
        score, feedback, level = 70, "ভালো উত্তর!", "ভালো"
    else:
        score, feedback, level = 88, "চমৎকার উত্তর!", "চমৎকার"
    return {"প্রশ্ন": input_data.question, "স্কোর": f"{score}/১০০", "লেভেল": level, "ফিডব্যাক": feedback}

# Tool 12: Learning Management
@app.post("/api/lms")
async def learning_management(input_data: TextInput):
    content = clean_text(input_data.text)
    summary = summarize_text(content)
    return {"পাঠের সারাংশ": summary, "মোট শব্দ": len(content.split()), "অগ্রগতি": f"{random.randint(50, 95)}%"}

# ==================== HTML UI (Client-side JavaScript with live time update) ====================

html_content = """<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>বাংলা এআই স্যুট | ১২টি টুল</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Hind Siliguri', sans-serif;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            min-height: 100vh;
        }
        .header {
            background: rgba(255,255,255,0.95);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .logo { display: flex; align-items: center; gap: 10px; }
        .logo-icon {
            width: 45px;
            height: 45px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.05); } }
        .logo-icon i { font-size: 24px; color: white; }
        .logo-text { font-size: 18px; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; background-clip: text; color: transparent; }
        .datetime-widget {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 6px 15px;
            border-radius: 30px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            font-size: 11px;
            flex-wrap: wrap;
        }
        .datetime-widget span { white-space: nowrap; }
        .container { max-width: 1400px; margin: 0 auto; padding: 15px; }
        .hero {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }
        .hero h1 { font-size: 20px; color: #1e3c72; margin-bottom: 5px; }
        .hero p { font-size: 12px; color: #555; }
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .tool-card {
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 10px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        .tool-card:hover { transform: translateY(-2px); box-shadow: 0 5px 12px rgba(0,0,0,0.1); }
        .tool-card.active { border-color: #667eea; background: linear-gradient(135deg, #fff, #f0f4ff); }
        .tool-icon { font-size: 28px; margin-bottom: 4px; }
        .tool-name { font-size: 10px; font-weight: 700; color: #1e3c72; }
        .main-panel {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 18px;
        }
        .panel-title { font-size: 18px; font-weight: 700; color: #667eea; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
        textarea {
            width: 100%;
            min-height: 140px;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-family: monospace;
            font-size: 13px;
            resize: vertical;
            outline: none;
        }
        textarea:focus { border-color: #667eea; }
        .extra-inputs { margin-top: 10px; }
        select, input {
            width: 100%;
            padding: 8px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 12px;
            margin-bottom: 6px;
        }
        .btn-group { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        .btn-primary { background: linear-gradient(135deg, #667eea, #764ba2); color: white; flex: 1; }
        .btn-primary:hover { transform: translateY(-1px); }
        .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
        .btn-secondary { background: #f0f0f0; color: #333; }
        .btn-secondary:hover { background: #e0e0e0; }
        .result-area {
            margin-top: 15px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 10px;
            display: none;
            max-height: 350px;
            overflow-y: auto;
        }
        .result-box {
            background: white;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
            font-size: 12px;
            line-height: 1.5;
        }
        .result-box strong { color: #667eea; display: block; margin-bottom: 5px; }
        .loader {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error-box {
            background: #f8d7da;
            border-left-color: #dc3545;
            color: #721c24;
        }
        .footer { text-align: center; padding: 12px; color: rgba(255,255,255,0.7); font-size: 10px; }
        @media (max-width: 768px) {
            .header { flex-direction: column; text-align: center; }
            .tools-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; }
            .tool-name { font-size: 9px; }
            .tool-icon { font-size: 24px; }
            .btn-group { flex-direction: column; }
            .btn-primary { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon"><i class="fas fa-brain"></i></div>
            <span class="logo-text">বাংলা এআই স্যুট</span>
        </div>
        <div class="datetime-widget" id="datetime-widget">
            <span id="greeting">শুভ সকাল</span>
            <span id="day-name">সোমবার</span>
            <span id="bangla-date">০১ বৈশাখ, ১৪৩০</span>
            <span id="time">১২:০০:০০ AM</span>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1><i class="fas fa-robot"></i> ১২টি বাংলা এআই টুল</h1>
            <p>সামারাইজ | সেন্টিমেন্ট | কীওয়ার্ড | কন্টেন্ট | ইমেইল | রিসার্চ | কোড | সোশ্যাল | মিটিং | রিজিউমে | ইন্টারভিউ | এলএমএস</p>
        </div>

        <div class="tools-grid" id="tools-grid"></div>

        <div class="main-panel">
            <div class="panel-title"><i class="fas fa-tools"></i> <span id="active-name">টেক্সট সামারাইজার</span></div>
            <textarea id="input-text" placeholder="এখানে আপনার টেক্সট লিখুন..."></textarea>
            <div id="extra-inputs" class="extra-inputs"></div>
            <div class="btn-group">
                <button class="btn btn-primary" id="processBtn" onclick="processText()"><i class="fas fa-play"></i> প্রসেস</button>
                <button class="btn btn-secondary" onclick="clearAll()"><i class="fas fa-trash"></i> ক্লিয়ার</button>
                <button class="btn btn-secondary" onclick="loadExample()"><i class="fas fa-file-alt"></i> উদাহরণ</button>
            </div>
            <div id="result-area" class="result-area">
                <div id="result-content"></div>
            </div>
        </div>
        <div class="footer">
            <p><i class="fas fa-heart"></i> ১২টি এআই টুল | সম্পূর্ণ ফ্রি | বাংলায় এআই</p>
        </div>
    </div>

    <script>
        // Live Time Update - প্রতি সেকেন্ডে আপডেট হবে
        function updateLiveTime() {
            const now = new Date();
            const hours = now.getHours();
            const minutes = now.getMinutes();
            const seconds = now.getSeconds();
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const formattedHours = hours % 12 || 12;
            const formattedMinutes = minutes.toString().padStart(2, '0');
            const formattedSeconds = seconds.toString().padStart(2, '0');
            const timeString = `${formattedHours}:${formattedMinutes}:${formattedSeconds} ${ampm}`;
            document.getElementById('time').innerHTML = timeString;
            
            // শুভেচ্ছা আপডেট
            if (hours < 12) {
                document.getElementById('greeting').innerHTML = 'শুভ সকাল';
            } else if (hours < 18) {
                document.getElementById('greeting').innerHTML = 'শুভ বিকাল';
            } else {
                document.getElementById('greeting').innerHTML = 'শুভ রাত্রি';
            }
        }
        
        // Bangla Date আপডেট (প্রতি 5 মিনিটে)
        async function updateBanglaDate() {
            try {
                const response = await fetch('/api/bangla-date');
                const data = await response.json();
                document.getElementById('day-name').innerHTML = data.day_name;
                document.getElementById('bangla-date').innerHTML = data.short_date;
            } catch(e) {
                console.error('Date update error:', e);
            }
        }
        
        // প্রতি সেকেন্ডে সময় আপডেট হবে
        setInterval(updateLiveTime, 1000);
        updateLiveTime();
        
        // প্রতি 5 মিনিটে তারিখ আপডেট
        updateBanglaDate();
        setInterval(updateBanglaDate, 300000);
        
        const tools = [
            { id: 'summarizer', icon: '📝', name: 'সামারাইজার', needExtra: false },
            { id: 'sentiment', icon: '😊', name: 'সেন্টিমেন্ট', needExtra: false },
            { id: 'keywords', icon: '🔑', name: 'কীওয়ার্ড', needExtra: false },
            { id: 'content-writer', icon: '✍️', name: 'কন্টেন্ট', needExtra: false },
            { id: 'email-response', icon: '📧', name: 'ইমেইল', needExtra: true, extraType: 'email' },
            { id: 'research-analyzer', icon: '🔬', name: 'রিসার্চ', needExtra: false },
            { id: 'code-documentation', icon: '💻', name: 'কোড', needExtra: false },
            { id: 'social-content', icon: '📱', name: 'সোশ্যাল', needExtra: false },
            { id: 'meeting-summarizer', icon: '📋', name: 'মিটিং', needExtra: false },
            { id: 'resume-parser', icon: '📄', name: 'রিজিউমে', needExtra: true, extraType: 'resume' },
            { id: 'interview-prep', icon: '🎯', name: 'ইন্টারভিউ', needExtra: true, extraType: 'interview' },
            { id: 'lms', icon: '📚', name: 'এলএমএস', needExtra: false }
        ];

        let currentTool = tools[0];

        function renderTools() {
            const grid = document.getElementById('tools-grid');
            if (!grid) return;
            grid.innerHTML = '';
            for (let i = 0; i < tools.length; i++) {
                const t = tools[i];
                const activeClass = t.id === currentTool.id ? 'active' : '';
                grid.innerHTML += `
                    <div class="tool-card ${activeClass}" onclick="selectTool('${t.id}')">
                        <div class="tool-icon">${t.icon}</div>
                        <div class="tool-name">${t.name}</div>
                    </div>
                `;
            }
        }

        function selectTool(toolId) {
            for (let i = 0; i < tools.length; i++) {
                if (tools[i].id === toolId) {
                    currentTool = tools[i];
                    break;
                }
            }
            renderTools();
            document.getElementById('active-name').innerHTML = currentTool.name;
            document.getElementById('result-area').style.display = 'none';
            document.getElementById('extra-inputs').innerHTML = '';
            
            if (currentTool.extraType === 'email') {
                document.getElementById('extra-inputs').innerHTML = `
                    <select id="email-tone">
                        <option value="professional">📧 প্রোফেশনাল</option>
                        <option value="casual">💬 ক্যাজুয়াল</option>
                    </select>
                `;
            } else if (currentTool.extraType === 'resume') {
                document.getElementById('extra-inputs').innerHTML = `
                    <input type="text" id="resume-name" placeholder="👤 নাম">
                    <input type="email" id="resume-email" placeholder="📧 ইমেইল">
                    <input type="text" id="resume-skills" placeholder="🔧 দক্ষতা (কমা দিয়ে)">
                    <textarea id="resume-experience" placeholder="💼 কাজের অভিজ্ঞতা" rows="2"></textarea>
                    <textarea id="resume-education" placeholder="🎓 শিক্ষাগত যোগ্যতা" rows="2"></textarea>
                `;
            } else if (currentTool.extraType === 'interview') {
                document.getElementById('extra-inputs').innerHTML = `
                    <select id="interview-question">
                        <option value="আপনি কে? আপনার পরিচয় দিন।">🤝 পরিচয় দিন</option>
                        <option value="আপনার কাজের অভিজ্ঞতা সম্পর্কে বলুন।">💼 কাজের অভিজ্ঞতা</option>
                        <option value="আপনার শক্তি কি কি?">⭐ আপনার শক্তি</option>
                    </select>
                    <textarea id="interview-answer" placeholder="✍️ আপনার উত্তর লিখুন..." rows="3"></textarea>
                `;
            }
        }

        async function processText() {
            const resultArea = document.getElementById('result-area');
            const resultContent = document.getElementById('result-content');
            const processBtn = document.getElementById('processBtn');
            
            resultArea.style.display = 'block';
            resultContent.innerHTML = '<div class="loader"></div> প্রসেসিং হচ্ছে...';
            if (processBtn) processBtn.disabled = true;
            
            try {
                let body = {};
                const toolId = currentTool.id;
                const text = document.getElementById('input-text').value;
                
                if (toolId === 'email-response') {
                    body = {
                        email_content: text || 'আমি আপনার প্রোডাক্ট সম্পর্কে জানতে চাই।',
                        tone: document.getElementById('email-tone')?.value || 'professional'
                    };
                } else if (toolId === 'resume-parser') {
                    body = {
                        name: document.getElementById('resume-name')?.value || 'জন দে',
                        email: document.getElementById('resume-email')?.value || 'john@example.com',
                        skills: document.getElementById('resume-skills')?.value || 'পাইথন, ডিজেঙ্গো',
                        experience: document.getElementById('resume-experience')?.value || '৫ বছর অভিজ্ঞতা',
                        education: document.getElementById('resume-education')?.value || 'বিএসসি সিএসই'
                    };
                } else if (toolId === 'interview-prep') {
                    body = {
                        question: document.getElementById('interview-question')?.value || 'আপনার পরিচয় দিন',
                        answer: document.getElementById('interview-answer')?.value || text || 'আমি একজন দক্ষ পেশাদার'
                    };
                } else {
                    if (!text.trim()) {
                        resultContent.innerHTML = '<div class="result-box error-box">❌ দয়া করে কিছু টেক্সট লিখুন</div>';
                        if (processBtn) processBtn.disabled = false;
                        return;
                    }
                    body = { text: text };
                }
                
                const response = await fetch(`/api/${toolId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const data = await response.json();
                
                let html = '';
                for (const [key, val] of Object.entries(data)) {
                    if (key !== 'status') {
                        if (Array.isArray(val)) {
                            html += `<div class="result-box"><strong>📌 ${key}:</strong><br>${val.map(v => `• ${v}`).join('<br>')}</div>`;
                        } else if (typeof val === 'object') {
                            html += `<div class="result-box"><strong>📌 ${key}:</strong><br><pre style="margin-top:5px;">${JSON.stringify(val, null, 2)}</pre></div>`;
                        } else {
                            html += `<div class="result-box"><strong>📌 ${key}:</strong><br>${val}</div>`;
                        }
                    }
                }
                resultContent.innerHTML = html || '<div class="result-box">✅ সম্পন্ন!</div>';
            } catch(err) {
                resultContent.innerHTML = `<div class="result-box error-box">❌ ${err.message}</div>`;
            } finally {
                if (processBtn) processBtn.disabled = false;
            }
        }

        function clearAll() {
            document.getElementById('input-text').value = '';
            document.getElementById('result-area').style.display = 'none';
            if (document.getElementById('interview-answer')) document.getElementById('interview-answer').value = '';
            if (document.getElementById('resume-name')) document.getElementById('resume-name').value = '';
            if (document.getElementById('resume-email')) document.getElementById('resume-email').value = '';
            if (document.getElementById('resume-skills')) document.getElementById('resume-skills').value = '';
            if (document.getElementById('resume-experience')) document.getElementById('resume-experience').value = '';
            if (document.getElementById('resume-education')) document.getElementById('resume-education').value = '';
        }

        function loadExample() {
            const examples = {
                summarizer: 'বাংলাদেশ একটি ছোট কিন্তু জনবহুল দেশ। এটি দক্ষিণ এশিয়ায় অবস্থিত। ঢাকা এর রাজধানী। এখানে অনেক প্রাকৃতিক সৌন্দর্য রয়েছে। সুন্দরবন বিশ্বের সবচেয়ে বড় ম্যানগ্রোভ বন। কক্সবাজার বিশ্বের দীর্ঘতম সমুদ্র সৈকত। বাংলাদেশের অর্থনীতি দ্রুত বাড়ছে।',
                sentiment: 'আপনার সার্ভিস খুব ভালো ছিল। দ্রুত ডেলিভারি এবং পেশাদার আচরণ সত্যিই চমৎকার। ধন্যবাদ!',
                'code-documentation': 'def add_numbers(a, b):\\n    return a + b',
                'email-response': 'আমি আপনার প্রোডাক্টটি কিনতে আগ্রহী। দয়া করে বিস্তারিত জানান।'
            };
            document.getElementById('input-text').value = examples[currentTool.id] || examples.summarizer;
        }

        renderTools();
        selectTool('summarizer');
    </script>
</body>
</html>
"""

@app.get("/")
async def home():
    return HTMLResponse(content=html_content)

# Vercel handler
handler = app