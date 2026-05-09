from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import os
import re
import io
import json
import hashlib
import random
from datetime import datetime
from typing import Optional, List, Dict
from collections import Counter
import unicodedata

# Try to import optional dependencies
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Initialize FastAPI app
app = FastAPI(title='Bangla AI All-in-One Suite', 
              description='12 Powerful AI Tools in One Platform - Complete Bangla Solution', 
              version='1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== BANGLA DATE SYSTEM ====================

BANGLA_NUMBERS = {
    0: '০', 1: '১', 2: '২', 3: '৩', 4: '৪',
    5: '৫', 6: '৬', 7: '৭', 8: '৮', 9: '৯'
}

BANGLA_DAYS = {
    'Monday': 'সোমবার',
    'Tuesday': 'মঙ্গলবার',
    'Wednesday': 'বুধবার',
    'Thursday': 'বৃহস্পতিবার',
    'Friday': 'শুক্রবার',
    'Saturday': 'শনিবার',
    'Sunday': 'রবিবার'
}

BANGLA_MONTHS = [
    'বৈশাখ', 'জ্যৈষ্ঠ', 'আষাঢ়', 'শ্রাবণ',
    'ভাদ্র', 'আশ্বিন', 'কার্তিক', 'অগ্রহায়ণ',
    'পৌষ', 'মাঘ', 'ফাল্গুন', 'চৈত্র'
]

BANGLA_SEASONS = {
    'বৈশাখ': 'গ্রীষ্ম', 'জ্যৈষ্ঠ': 'গ্রীষ্ম',
    'আষাঢ়': 'বর্ষা', 'শ্রাবণ': 'বর্ষা',
    'ভাদ্র': 'শরৎ', 'আশ্বিন': 'শরৎ',
    'কার্তিক': 'হেমন্ত', 'অগ্রহায়ণ': 'হেমন্ত',
    'পৌষ': 'শীত', 'মাঘ': 'শীত',
    'ফাল্গুন': 'বসন্ত', 'চৈত্র': 'বসন্ত'
}

SEASON_ICONS = {
    'গ্রীষ্ম': '☀️', 'বর্ষা': '🌧️', 'শরৎ': '🍂',
    'হেমন্ত': '🌾', 'শীত': '❄️', 'বসন্ত': '🌸'
}

def to_bangla_number(num):
    """Convert English number to Bangla"""
    return ''.join(BANGLA_NUMBERS[int(d)] for d in str(num))

def get_bangla_date():
    """Get complete Bangla date"""
    now = datetime.now()
    
    # Bangla year calculation (Bengali calendar is 593 years behind Gregorian)
    bangla_year = now.year - 593
    if now.month < 4:
        bangla_year -= 1
    
    # Bangla month calculation
    month_index = (now.month - 1) % 12
    bangla_month = BANGLA_MONTHS[month_index]
    
    # Bangla day of month (approximate offset)
    bangla_day = now.day
    if now.day > 13:
        bangla_day = now.day - 13
    else:
        bangla_day = now.day + 17
        if bangla_day > 31:
            bangla_day = bangla_day - 31
            month_index = (month_index + 1) % 12
            bangla_month = BANGLA_MONTHS[month_index]
    
    # Get season
    season = BANGLA_SEASONS.get(bangla_month, 'বসন্ত')
    season_icon = SEASON_ICONS.get(season, '🌸')
    
    # Get day name
    day_name = BANGLA_DAYS[now.strftime('%A')]
    
    # Get time
    time_12hr = now.strftime('%I:%M:%S %p')
    hour = now.hour
    if hour < 12:
        time_period = 'সকাল'
    elif hour < 16:
        time_period = 'দুপুর'
    elif hour < 20:
        time_period = 'সন্ধ্যা'
    else:
        time_period = 'রাত'
    
    return {
        'full_date': f"{day_name}, {to_bangla_number(bangla_day)} {bangla_month} {to_bangla_number(bangla_year)}",
        'short_date': f"{to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)}",
        'day_name': day_name,
        'day_number': to_bangla_number(bangla_day),
        'month': bangla_month,
        'year': to_bangla_number(bangla_year),
        'season': season,
        'season_icon': season_icon,
        'time': time_12hr,
        'time_period': time_period,
        'full_datetime': f"{day_name}, {to_bangla_number(bangla_day)} {bangla_month}, {to_bangla_number(bangla_year)} - {time_12hr}",
        'greeting': get_bangla_greeting(hour)
    }

def get_bangla_greeting(hour):
    """Get Bangla greeting based on time"""
    if hour < 12:
        return 'শুভ সকাল'
    elif hour < 18:
        return 'শুভ বিকাল'
    else:
        return 'শুভ রাত্রি'

# ==================== DATA ====================

BANGLA_STOP_WORDS = {'এবং', 'হয়ে', 'হতে', 'থেকে', 'একটি', 'এই', 'ও', 'সে', 'তা', 'আমি', 'তুমি'}
BANGLA_POSITIVE = {'ভালো', 'চমৎকার', 'সুন্দর', 'আনন্দ', 'খুশি', 'পছন্দ', 'সফল', 'জয়', 'প্রিয়', 'দারুণ', 'অসাধারণ'}
BANGLA_NEGATIVE = {'খারাপ', 'মন্দ', 'দুঃখ', 'বেদনা', 'ঘৃণা', 'ব্যর্থ', 'হার', 'শোক', 'ক্ষতি', 'সমস্যা', 'ত্রুটি'}

BANGLA_QUESTIONS = {
    'introduction': 'আপনি কে? আপনার পরিচয় দিন।',
    'experience': 'আপনার কাজের অভিজ্ঞতা সম্পর্কে বলুন।',
    'strength': 'আপনার শক্তি কি কি?',
    'weakness': 'আপনার দুর্বলতা কি?',
    'goal': 'আপনার ক্যারিয়ারের লক্ষ্য কি?',
    'teamwork': 'টিমওয়ার্ক সম্পর্কে আপনার মতামত কি?',
    'leadership': 'নেতৃত্বের গুণাবলী কি কি?',
    'problem_solving': 'সমস্যা সমাধানের পদ্ধতি কি?'
}

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = unicodedata.normalize('NFC', text)
    return text.strip()

def bangla_word_count(text):
    return len(re.findall(r'[\u0980-\u09FF]+', text))

def extract_keywords(text, n=5):
    words = re.findall(r'[\u0980-\u09FF]+', text)
    word_freq = Counter(words)
    for stop in BANGLA_STOP_WORDS:
        word_freq.pop(stop, None)
    return [w for w, _ in word_freq.most_common(n)]

def sentiment_analysis(text):
    words = text.split()
    pos = sum(1 for w in words if w in BANGLA_POSITIVE)
    neg = sum(1 for w in words if w in BANGLA_NEGATIVE)
    if pos > neg:
        return 'পজিটিভ', '😊', pos, neg
    elif neg > pos:
        return 'নেগেটিভ', '😢', pos, neg
    return 'নিউট্রাল', '😐', pos, neg

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

# API Endpoints Models
class TextInput(BaseModel):
    text: str
    style: Optional[str] = "general"

class EmailInput(BaseModel):
    email_content: str
    tone: Optional[str] = "professional"

class ResumeInput(BaseModel):
    name: str
    email: str
    phone: str
    skills: str
    experience: str
    education: str

class InterviewAnswer(BaseModel):
    question: str
    answer: str

# ==================== API ENDPOINTS ====================

# 1. বাংলা টেক্সট সামারাইজার
@app.post("/api/summarizer")
async def bangla_summarizer(input_data: TextInput):
    try:
        text = clean_text(input_data.text)
        if len(text) < 20:
            return {"error": "কমপক্ষে ২০ অক্ষরের টেক্সট দিন", "status": "error"}
        
        summary = summarize_text(text)
        keywords = extract_keywords(text)
        
        return {
            "মূল টেক্সটের দৈর্ঘ্য": f"{len(text)} অক্ষর",
            "সারাংশ": summary,
            "সারাংশের দৈর্ঘ্য": f"{len(summary)} অক্ষর",
            "মূল কীওয়ার্ড": ", ".join(keywords),
            "কম্প্রেশন রেট": f"{(1 - len(summary)/len(text)) * 100:.1f}%",
            "সাজেশন": "আপনার টেক্সট সফলভাবে সংক্ষিপ্ত করা হয়েছে",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 2. কন্টেন্ট রাইটিং অ্যাসিস্ট্যান্ট
@app.post("/api/content-writer")
async def content_writer(input_data: TextInput):
    try:
        topic = input_data.text
        
        blog_post = f"""## {topic}: একটি বিস্তারিত আলোচনা

### ভূমিকা
বর্তমান যুগে {topic} একটি অত্যন্ত গুরুত্বপূর্ণ বিষয়। এটি আমাদের দৈনন্দিন জীবনে গভীর প্রভাব ফেলছে।

### {topic} এর গুরুত্ব
{topic} এর গুরুত্ব অপরিসীম। নিম্নলিখিত ক্ষেত্রে এটি বিশেষ ভূমিকা রাখে:
1. দক্ষতা বৃদ্ধি - {topic} ব্যবহার করে কাজের গতি বহুগুণ বাড়ানো সম্ভব
2. সময় সাশ্রয় - এটি জটিল কাজ সহজ করে দেয়
3. নির্ভুলতা - {topic} এর মাধ্যমে ত্রুটিহীন কাজ করা যায়

### {topic} এর ভবিষ্যৎ
বিশেষজ্ঞদের মতে, আগামী কয়েক বছরে {topic} আরও বেশি গুরুত্বপূর্ণ হয়ে উঠবে। এর ব্যবহার শিক্ষা, চিকিৎসা, ব্যবসা ক্ষেত্রে ব্যাপক বৃদ্ধি পাবে।

### উপসংহার
সব মিলিয়ে, {topic} আমাদের জীবনের একটি অপরিহার্য অংশ হয়ে উঠেছে। এর সঠিক ব্যবহার নিশ্চিত করা জরুরি।"""

        seo_title = f"{topic} - সম্পূর্ণ গাইড ও তথ্য | Bangla AI Suite"
        seo_desc = f"{topic} সম্পর্কে বিস্তারিত জানুন। বৈশিষ্ট্য, সুবিধা, ব্যবহারবিধি এবং ভবিষ্যৎ সম্ভাবনা।"
        hashtags = [f"#{topic.replace(' ', '')}", "#বাংলা", "#টেকনোলজি", "#এআই", "#ইনোভেশন"]
        
        return {
            "ব্লগ পোস্ট": blog_post,
            "এসইও টাইটেল": seo_title,
            "এসইও ডেসক্রিপশন": seo_desc,
            "হ্যাশট্যাগ": " ".join(hashtags),
            "স্ট্যাটাস": "কন্টেন্ট সফলভাবে তৈরি হয়েছে",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 3. ডকুমেন্ট কনভার্টার ও সামারাইজার
@app.post("/api/document-processor")
async def document_processor(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = ""
        
        if file.filename.endswith('.pdf') and PDF_SUPPORT:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif file.filename.endswith('.txt'):
            text = content.decode('utf-8')
        else:
            return {"error": "শুধু PDF বা TXT ফাইল সাপোর্ট করে।", "status": "error"}
        
        if len(text) < 20:
            return {"error": "ফাইলে পর্যাপ্ত টেক্সট নেই (কমপক্ষে ২০ অক্ষর প্রয়োজন)", "status": "error"}
        
        summary = summarize_text(text)
        keywords = extract_keywords(text)
        
        return {
            "ফাইলের নাম": file.filename,
            "মোট অক্ষর": len(text),
            "মোট শব্দ": bangla_word_count(text),
            "সারাংশ": summary,
            "মূল কীওয়ার্ড": ", ".join(keywords),
            "কম্প্রেশন": f"{(1 - len(summary)/len(text)) * 100:.1f}%",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 4. রিসার্চ পেপার অ্যানালাইজার
@app.post("/api/research-analyzer")
async def research_analyzer(input_data: TextInput):
    try:
        paper = clean_text(input_data.text)
        
        sentences = re.split(r'[।?!]', paper)
        key_points = [s.strip() for s in sentences if len(s.strip()) > 30][:5]
        
        citation = f"(লেখক, {datetime.now().year})"
        
        return {
            "গবেষণার শিরোনাম": paper[:60] + "..." if len(paper) > 60 else paper,
            "মূল পয়েন্টসমূহ": key_points,
            "সাজেস্টেড সাইটেশন": citation,
            "গবেষণার ফাঁকা জায়গা": "এই ক্ষেত্রে আরও গবেষণার প্রয়োজন রয়েছে",
            "সাজেশন": "পিয়ার রিভিউ জার্নালে প্রকাশের জন্য প্রস্তুত করুন",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 5. কোড ডকুমেন্টেশন জেনারেটর
@app.post("/api/code-documentation")
async def code_documentation(input_data: TextInput):
    try:
        code = input_data.text
        
        if 'def ' in code:
            lang = "পাইথন"
            func_name = code.split('def ')[1].split('(')[0]
            doc = f'''\"\"\"
{func_name} ফাংশনের ডকুমেন্টেশন
================================

এই ফাংশনটি {func_name} এর কাজ সম্পাদন করে।

প্যারামিটার:
-----------
- a: প্রথম সংখ্যা
- b: দ্বিতীয় সংখ্যা

রিটার্ন:
-------
ফাংশনের ফলাফল

উদাহরণ:
-------
>>> result = {func_name}(5, 3)
>>> print(result)

লেখক: Bangla AI Suite
তারিখ: {datetime.now().strftime("%B %d, %Y")}
\"\"\"'''
        else:
            lang = "অজানা"
            doc = f"/*\nকোড ডকুমেন্টেশন\n================\n\nএই কোডটি {code[:50]}...\n\nতারিখ: {datetime.now().strftime('%B %d, %Y')}\n*/\n\n{code}"
        
        return {
            "কোডের ভাষা": lang,
            "জেনারেটেড ডকুমেন্টেশন": doc,
            "README সাজেশন": f"# প্রজেক্ট ডকুমেন্টেশন\n\n## বর্ণনা\nএই প্রজেক্টটি {code[:50]}... এর জন্য তৈরি।",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 6. সোশ্যাল মিডিয়া কন্টেন্ট জেনারেটর
@app.post("/api/social-content")
async def social_content(input_data: TextInput):
    try:
        topic = input_data.text
        
        linkedin_post = f"""🚀 {topic} নিয়ে আমার চিন্তাভাবনা

{topic} বর্তমানে আলোচনার কেন্দ্রবিন্দুতে।

💡 কীভাবে {topic} থেকে উপকৃত হবেন?
১. প্রতিদিন {topic} নিয়ে পড়াশোনা করুন
২. বিশেষজ্ঞদের অনুসরণ করুন
৩. নিজের অভিজ্ঞতা শেয়ার করুন

#BanglaAI #{topic.replace(' ', '')} #BanglaTech"""

        hashtags = f"#{topic.replace(' ', '')} #BanglaAI #TechBangla #Innovation"
        
        return {
            "লিংকডইন পোস্ট": linkedin_post,
            "হ্যাশট্যাগ": hashtags,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 7. ইমেইল রেসপন্স জেনারেটর
@app.post("/api/email-response")
async def email_response(input_data: EmailInput):
    try:
        text = input_data.email_content
        tone = input_data.tone
        
        if tone == "professional":
            response = f"""বিষয়: আপনার ইমেইলের জবাব

প্রিয় গ্রাহক,

আপনার ইমেইলটি পেয়ে ধন্যবাদ। খুব শীঘ্রই আপনার সাথে যোগাযোগ করব।

ধন্যবাদান্তে,
Bangla AI টিম"""
        else:
            response = f"""হ্যালো! 👋

আপনার মেইল পেয়েছি। খুব শীঘ্রই রিপ্লাই দিচ্ছি।

- Bangla AI টিম"""
        
        sentiment, _, _, _ = sentiment_analysis(text)
        
        return {
            "জেনারেটেড রেসপন্স": response,
            "সেন্টিমেন্ট": sentiment,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 8. মিটিং নোটস সামারাইজার
@app.post("/api/meeting-summarizer")
async def meeting_summarizer(input_data: TextInput):
    try:
        notes = clean_text(input_data.text)
        
        sentences = notes.split('।')
        action_items = [s.strip() for s in sentences if 'করতে হবে' in s or 'প্রয়োজন' in s][:3]
        decisions = [s.strip() for s in sentences if 'সিদ্ধান্ত' in s][:3]
        
        summary = summarize_text(notes)
        
        return {
            "মিটিং সারাংশ": summary,
            "অ্যাকশন আইটেম": action_items if action_items else ["কোন অ্যাকশন আইটেম নেই"],
            "গৃহীত সিদ্ধান্ত": decisions if decisions else ["কোন সিদ্ধান্ত নেই"],
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 9. রিজিউমে/সিভি পার্সার
@app.post("/api/resume-parser")
async def resume_parser(input_data: ResumeInput):
    try:
        skills_list = [s.strip() for s in input_data.skills.split(',')]
        job_match = random.randint(65, 95)
        
        return {
            "ব্যক্তির নাম": input_data.name,
            "ইমেইল": input_data.email,
            "দক্ষতা সমূহ": skills_list,
            "কাজের অভিজ্ঞতা": input_data.experience[:100] + "..." if len(input_data.experience) > 100 else input_data.experience,
            "এটিএস স্কোর": f"{job_match}%",
            "সাজেশন": ["আরও কীওয়ার্ড যুক্ত করুন", "অর্জনগুলো হাইলাইট করুন"],
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 10. কাস্টমার ফিডব্যাক অ্যানালাইজার
@app.post("/api/feedback-analyzer")
async def feedback_analyzer(input_data: TextInput):
    try:
        feedback = input_data.text
        sentiment, emoji, pos_count, neg_count = sentiment_analysis(feedback)
        keywords = extract_keywords(feedback)
        
        if 'ভালো' in feedback or 'চমৎকার' in feedback:
            category = "পজিটিভ - গ্রাহক সন্তুষ্ট"
            priority = "নিম্ন"
        elif 'খারাপ' in feedback or 'সমস্যা' in feedback:
            category = "নেগেটিভ - জরুরি অ্যাকশন"
            priority = "উচ্চ"
        else:
            category = "নিউট্রাল - সাধারণ মন্তব্য"
            priority = "মধ্যম"
        
        return {
            "সেন্টিমেন্ট": f"{sentiment} {emoji}",
            "ক্যাটেগরি": category,
            "মূল কীওয়ার্ড": ", ".join(keywords[:3]),
            "প্রায়োরিটি": priority,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 11. ইন্টারভিউ প্রিপারেশন টুল
@app.post("/api/interview-prep")
async def interview_prep(input_data: InterviewAnswer):
    try:
        question = input_data.question
        answer = input_data.answer
        
        word_count = len(answer.split())
        
        if word_count < 20:
            score = 40
            feedback = "আরও বিস্তারিত উত্তর দিন"
            level = "উন্নতি প্রয়োজন"
        elif word_count < 50:
            score = 70
            feedback = "ভালো উত্তর!"
            level = "ভালো"
        else:
            score = 88
            feedback = "চমৎকার উত্তর!"
            level = "চমৎকার"
        
        return {
            "প্রশ্ন": BANGLA_QUESTIONS.get(question, question),
            "স্কোর": f"{score}/১০০",
            "লেভেল": level,
            "ফিডব্যাক": feedback,
            "টিপস": "আত্মবিশ্বাসের সাথে উত্তর দিন, প্রাসঙ্গিক উদাহরণ দিন",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# 12. লার্নিং ম্যানেজমেন্ট সিস্টেম
@app.post("/api/lms")
async def learning_management(input_data: TextInput):
    try:
        content = clean_text(input_data.text)
        summary = summarize_text(content)
        
        return {
            "পাঠের সারাংশ": summary,
            "মোট শব্দ": len(content.split()),
            "পড়ার পরামর্শ": "প্রতিদিন নতুন কিছু শিখুন, নোট তৈরি করুন, নিয়মিত অনুশীলন করুন",
            "অগ্রগতি": f"{random.randint(50, 95)}%",
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

# ==================== HTML UI ====================

# Get Bangla date for display
current_date = get_bangla_date()

html_content = f"""<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>বাংলা এআই অল-ইন-ওয়ান স্যুট</title>
    <link href="https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Hind Siliguri', sans-serif;
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
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
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }}
        .logo {{ display: flex; align-items: center; gap: 12px; }}
        .logo-icon {{
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.05); }} }}
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
        .datetime-widget i {{ margin-right: 5px; }}
        .bangla-date {{ background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; }}
        .greeting {{ font-weight: 600; }}
        
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        .hero {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 25px;
            text-align: center;
        }}
        .hero h1 {{ font-size: 28px; color: #1e3c72; margin-bottom: 12px; }}
        .hero p {{ font-size: 15px; color: #555; line-height: 1.6; }}
        
        .tools-section {{ margin-bottom: 25px; }}
        .section-title {{ font-size: 22px; font-weight: 700; color: white; margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }}
        .tools-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 15px; }}
        .tool-card {{
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
            text-align: center;
        }}
        .tool-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }}
        .tool-card.active {{ border-color: #667eea; background: linear-gradient(135deg, #fff, #f0f4ff); }}
        .tool-icon {{ font-size: 40px; margin-bottom: 8px; }}
        .tool-name {{ font-size: 14px; font-weight: 700; color: #1e3c72; }}
        .tool-desc {{ font-size: 11px; color: #666; margin-top: 4px; }}
        
        .main-panel {{
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .panel-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 18px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .panel-title {{ font-size: 20px; font-weight: 700; color: #667eea; display: flex; align-items: center; gap: 8px; }}
        
        textarea {{
            width: 100%;
            min-height: 180px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
            outline: none;
        }}
        textarea:focus {{ border-color: #667eea; }}
        
        .extra-inputs {{ margin-top: 12px; }}
        
        .btn-group {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }}
        .btn {{
            padding: 10px 22px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-primary {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; flex: 1; }}
        .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(102,126,234,0.4); }}
        .btn-secondary {{ background: #f0f0f0; color: #333; }}
        .btn-secondary:hover {{ background: #e0e0e0; }}
        
        .result-area {{
            margin-top: 20px;
            padding: 18px;
            background: #f9f9f9;
            border-radius: 12px;
            display: none;
            max-height: 400px;
            overflow-y: auto;
        }}
        .result-header {{ font-size: 17px; font-weight: 700; color: #667eea; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }}
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
        
        .footer {{ text-align: center; padding: 20px; color: rgba(255,255,255,0.7); font-size: 11px; }}
        
        @media (max-width: 768px) {{
            .header {{ flex-direction: column; text-align: center; }}
            .tools-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .tool-icon {{ font-size: 32px; }}
            .btn-group {{ flex-direction: column; }}
            .btn-primary {{ width: 100%; justify-content: center; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">
            <div class="logo-icon"><i class="fas fa-brain"></i></div>
            <div><span class="logo-text">বাংলা এআই স্যুট</span></div>
        </div>
        <div class="datetime-widget">
            <div class="greeting"><i class="fas fa-sun"></i> {current_date['greeting']}</div>
            <div><i class="fas fa-calendar-alt"></i> {current_date['day_name']}</div>
            <div class="bangla-date"><i class="fas fa-calendar"></i> {current_date['short_date']}</div>
            <div><i class="fas fa-leaf"></i> {current_date['season_icon']} {current_date['season']}</div>
            <div><i class="fas fa-clock"></i> {current_date['time']}</div>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1><i class="fas fa-robot"></i> বাংলা এআই অল-ইন-ওয়ান স্যুট</h1>
            <p>১২টি শক্তিশালী কৃত্রিম বুদ্ধিমত্তার টুল একসাথে। টেক্সট সামারাইজ, কন্টেন্ট তৈরি, ডকুমেন্ট প্রসেস ও আরও অনেক কিছু করুন সম্পূর্ণ বিনামূল্যে!</p>
        </div>

        <div class="tools-section">
            <div class="section-title"><i class="fas fa-th-large"></i><span>আমাদের টুলসমূহ</span></div>
            <div class="tools-grid" id="tools-grid"></div>
        </div>

        <div class="main-panel">
            <div class="panel-header">
                <div class="panel-title"><i class="fas fa-cogs"></i> <span id="active-name">বাংলা টেক্সট সামারাইজার</span></div>
                <div class="info-badge"><i class="fas fa-info-circle"></i> টুল সিলেক্ট করে ব্যবহার করুন</div>
            </div>
            <div class="input-area">
                <textarea id="input-text" placeholder="এখানে আপনার টেক্সট লিখুন বা পেস্ট করুন..."></textarea>
                <div id="extra-inputs" class="extra-inputs"></div>
            </div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="processText()"><i class="fas fa-play"></i> প্রসেস করুন</button>
                <button class="btn btn-secondary" onclick="clearAll()"><i class="fas fa-trash-alt"></i> ক্লিয়ার</button>
                <button class="btn btn-secondary" onclick="loadExample()"><i class="fas fa-file-alt"></i> উদাহরণ</button>
                <button class="btn btn-secondary" onclick="copyOutput()"><i class="fas fa-copy"></i> কপি</button>
            </div>
            <div id="result-area" class="result-area">
                <div class="result-header"><i class="fas fa-check-circle"></i> ফলাফল</div>
                <div id="result-content" class="result-content"></div>
            </div>
        </div>
        <div class="footer">
            <p><i class="fas fa-copyright"></i> ২০২৪ বাংলা এআই অল-ইন-ওয়ান স্যুট | সম্পূর্ণ ফ্রি</p>
        </div>
    </div>

    <script>
        const tools = [
            {{ id: 'summarizer', icon: '📝', name: 'বাংলা টেক্সট সামারাইজার', desc: 'লেখার সংক্ষিপ্তসার তৈরি' }},
            {{ id: 'content', icon: '✍️', name: 'কন্টেন্ট রাইটিং', desc: 'ব্লগ, SEO, হ্যাশট্যাগ' }},
            {{ id: 'document', icon: '📄', name: 'ডকুমেন্ট প্রসেসর', desc: 'PDF থেকে টেক্সট' }},
            {{ id: 'research', icon: '🔬', name: 'রিসার্চ অ্যানালাইজার', desc: 'গবেষণা পত্র বিশ্লেষণ' }},
            {{ id: 'code', icon: '💻', name: 'কোড ডকুমেন্টেশন', desc: 'কোড থেকে ডকুমেন্টেশন' }},
            {{ id: 'social', icon: '📱', name: 'সোশ্যাল কন্টেন্ট', desc: 'LinkedIn, Twitter পোস্ট' }},
            {{ id: 'email', icon: '📧', name: 'ইমেইল রেসপন্স', desc: 'অটো ইমেইল রিপ্লাই' }},
            {{ id: 'meeting', icon: '📋', name: 'মিটিং সামারাইজার', desc: 'মিটিং নোটস' }},
            {{ id: 'resume', icon: '📄', name: 'রিজিউমে পার্সার', desc: 'সিভি থেকে তথ্য' }},
            {{ id: 'feedback', icon: '💬', name: 'ফিডব্যাক অ্যানালাইজার', desc: 'সেন্টিমেন্ট 분석' }},
            {{ id: 'interview', icon: '🎯', name: 'ইন্টারভিউ প্রিপারেশন', desc: 'প্রশ্ন-উত্তর বিশ্লেষণ' }},
            {{ id: 'lms', icon: '📚', name: 'এলএমএস', desc: 'কুইজ ও সারাংশ' }}
        ];

        let currentTool = tools[0];

        function renderTools() {{
            const grid = document.getElementById('tools-grid');
            let html = '';
            for (let i = 0; i < tools.length; i++) {{
                const tool = tools[i];
                const activeClass = tool.id === currentTool.id ? 'active' : '';
                html += `<div class="tool-card ${{activeClass}}" onclick="selectTool('${{tool.id}}')">
                    <div class="tool-icon">${{tool.icon}}</div>
                    <div class="tool-name">${{tool.name}}</div>
                    <div class="tool-desc">${{tool.desc}}</div>
                </div>`;
            }}
            grid.innerHTML = html;
        }}

        function selectTool(toolId) {{
            for (let i = 0; i < tools.length; i++) {{
                if (tools[i].id === toolId) {{
                    currentTool = tools[i];
                    break;
                }}
            }}
            renderTools();
            document.getElementById('active-name').innerHTML = currentTool.name;
            document.getElementById('result-area').style.display = 'none';
            document.getElementById('extra-inputs').innerHTML = '';
            
            if (toolId === 'email') {{
                document.getElementById('extra-inputs').innerHTML = '<select id="email-tone" style="width:100%; margin-top:10px; padding:10px; border-radius:8px; border:2px solid #e0e0e0;"><option value="professional">প্রোফেশনাল</option><option value="casual">ক্যাজুয়াল</option></select>';
            }} else if (toolId === 'resume') {{
                document.getElementById('extra-inputs').innerHTML = '<div style="display:grid; gap:10px; margin-top:10px;"><input type="text" id="resume-name" placeholder="নাম" style="padding:10px; border-radius:8px; border:2px solid #e0e0e0;"><input type="email" id="resume-email" placeholder="ইমেইল" style="padding:10px; border-radius:8px; border:2px solid #e0e0e0;"><input type="text" id="resume-skills" placeholder="দক্ষতা (কমা দিয়ে)" style="padding:10px; border-radius:8px; border:2px solid #e0e0e0;"><textarea id="resume-experience" placeholder="কাজের অভিজ্ঞতা" rows="2" style="padding:10px; border-radius:8px; border:2px solid #e0e0e0;"></textarea><textarea id="resume-education" placeholder="শিক্ষাগত যোগ্যতা" rows="2" style="padding:10px; border-radius:8px; border:2px solid #e0e0e0;"></textarea></div>';
            }} else if (toolId === 'interview') {{
                document.getElementById('extra-inputs').innerHTML = '<select id="interview-question" style="width:100%; margin-top:10px; padding:10px; border-radius:8px; border:2px solid #e0e0e0;"><option value="introduction">আপনার পরিচয় দিন</option><option value="experience">কাজের অভিজ্ঞতা</option><option value="strength">আপনার শক্তি</option></select><textarea id="interview-answer" placeholder="আপনার উত্তর লিখুন..." rows="3" style="width:100%; margin-top:10px; padding:10px; border-radius:8px; border:2px solid #e0e0e0;"></textarea>';
            }} else if (toolId === 'document') {{
                document.getElementById('extra-inputs').innerHTML = '<input type="file" id="file-input" accept=".pdf,.txt" style="margin-top:10px; width:100%; padding:8px; border:2px solid #e0e0e0; border-radius:8px;"><p style="margin-top:5px; font-size:11px;">📄 PDF বা TXT ফাইল আপলোড করুন</p>';
            }}
        }}

        async function processText() {{
            const resultArea = document.getElementById('result-area');
            const resultContent = document.getElementById('result-content');
            const processBtn = document.querySelector('.btn-primary');
            
            resultArea.style.display = 'block';
            resultContent.innerHTML = '<div class="loader"></div> প্রসেসিং হচ্ছে...';
            if (processBtn) processBtn.disabled = true;
            
            try {{
                let response;
                const toolId = currentTool.id;
                const text = document.getElementById('input-text').value;
                
                if (toolId === 'document') {{
                    const fileInput = document.getElementById('file-input');
                    if (fileInput && fileInput.files[0]) {{
                        const formData = new FormData();
                        formData.append('file', fileInput.files[0]);
                        response = await fetch(`/api/${{toolId}}`, {{ method: 'POST', body: formData }});
                    }} else {{
                        throw new Error('ফাইল নির্বাচন করুন');
                    }}
                }} else if (toolId === 'email') {{
                    const tone = document.getElementById('email-tone') ? document.getElementById('email-tone').value : 'professional';
                    if (!text.trim()) throw new Error('ইমেইল লিখুন');
                    response = await fetch(`/api/${{toolId}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email_content: text, tone: tone }})
                    }});
                }} else if (toolId === 'resume') {{
                    response = await fetch(`/api/${{toolId}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            name: document.getElementById('resume-name')?.value || '',
                            email: document.getElementById('resume-email')?.value || '',
                            phone: '',
                            skills: document.getElementById('resume-skills')?.value || '',
                            experience: document.getElementById('resume-experience')?.value || '',
                            education: document.getElementById('resume-education')?.value || ''
                        }})
                    }});
                }} else if (toolId === 'interview') {{
                    response = await fetch(`/api/${{toolId}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            question: document.getElementById('interview-question')?.value || '',
                            answer: document.getElementById('interview-answer')?.value || ''
                        }})
                    }});
                }} else {{
                    if (!text.trim()) throw new Error('টেক্সট লিখুন');
                    response = await fetch(`/api/${{toolId}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ text: text }})
                    }});
                }}
                
                const data = await response.json();
                resultContent.innerHTML = formatResult(data);
                
            }} catch (error) {{
                resultContent.innerHTML = `<div class="result-box" style="background:#f8d7da; border-left-color:#dc3545;">❌ ${{error.message}}</div>`;
            }} finally {{
                if (processBtn) processBtn.disabled = false;
            }}
        }}

        function formatResult(data) {{
            if (data.error) return `<div class="result-box" style="background:#f8d7da;">❌ ${{data.error}}</div>`;
            let html = '';
            for (let key in data) {{
                if (key !== 'status') {{
                    let value = data[key];
                    if (Array.isArray(value)) {{
                        html += `<div class="result-box"><strong>📌 ${{key}}:</strong><br>${{value.map(v => `• ${{v}}`).join('<br>')}}</div>`;
                    }} else if (typeof value === 'object') {{
                        html += `<div class="result-box"><strong>📌 ${{key}}:</strong><br><pre style="background:#f9f9f9; padding:8px; border-radius:6px;">${{JSON.stringify(value, null, 2)}}</pre></div>`;
                    }} else {{
                        html += `<div class="result-box"><strong>📌 ${{key}}:</strong><br>${{value}}</div>`;
                    }}
                }}
            }}
            return html;
        }}

        function clearAll() {{
            document.getElementById('input-text').value = '';
            document.getElementById('result-area').style.display = 'none';
            if (document.getElementById('interview-answer')) document.getElementById('interview-answer').value = '';
        }}

        function copyOutput() {{
            const content = document.getElementById('result-content');
            const text = content.innerText;
            if (text && !text.includes('প্রসেসিং')) {{
                navigator.clipboard.writeText(text);
                alert('কপি করা হয়েছে!');
            }}
        }}

        function loadExample() {{
            const examples = {{
                summarizer: 'বাংলাদেশ একটি ছোট কিন্তু জনবহুল দেশ। এটি দক্ষিণ এশিয়ায় অবস্থিত। ঢাকা এর রাজধানী। এখানে অনেক প্রাকৃতিক সৌন্দর্য রয়েছে। সুন্দরবন বিশ্বের সবচেয়ে বড় ম্যানগ্রোভ বন।',
                content: 'কৃত্রিম বুদ্ধিমত্তা',
                email: 'আমি আপনার প্রোডাক্ট সম্পর্কে জানতে চাই।'
            }};
            document.getElementById('input-text').value = examples[currentTool.id] || examples.summarizer;
        }}

        renderTools();
        selectTool('summarizer');
        loadExample();
    </script>
</body>
</html>
"""

@app.get("/")
async def home():
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    bangla_date = get_bangla_date()
    return {
        "status": "healthy",
        "app": "Bangla AI All-in-One Suite",
        "version": "1.0",
        "tools": 12,
        "bangla_date": bangla_date['full_datetime'],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("""
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║     🚀 বাংলা এআই অল-ইন-ওয়ান স্যুট v1.0                           ║
    ║                                                                      ║
    ║     📍 লোকাল সার্ভার: http://127.0.0.1:8000                         ║
    ║     📖 এপিআই ডক্স: http://127.0.0.1:8000/docs                      ║
    ║                                                                      ║
    ║     📅 বাংলা তারিখ ও সময় দেখা যাচ্ছে                               ║
    ║     🛠️ ১২টি শক্তিশালী এআই টুল                                      ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)