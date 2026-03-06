#!/usr/bin/env python3
"""
AI Resume Analyzer - Flask Backend
Features: ATS Score, Skill Gap Analysis, Job Matching, Resume Rewriting, LinkedIn Suggestions
"""
import os, json, re, io
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, PyPDF2, docx

app = Flask(__name__)
CORS(app)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

TECH_SKILLS = {
    "programming": ["python","javascript","typescript","java","c++","c#","go","rust","ruby","php","swift","kotlin","scala","r","bash"],
    "web": ["react","angular","vue","node.js","express","django","flask","fastapi","html","css","next.js","graphql","rest api"],
    "data": ["sql","postgresql","mysql","mongodb","redis","elasticsearch","pandas","numpy","scikit-learn","tensorflow","pytorch","spark","kafka"],
    "cloud": ["aws","azure","gcp","docker","kubernetes","terraform","ansible","jenkins","ci/cd","devops","linux","nginx"],
    "ai_ml": ["machine learning","deep learning","nlp","computer vision","llm","langchain","openai","hugging face","rag"],
    "tools": ["git","jira","confluence","figma","postman","tableau","power bi","excel","agile","scrum"]
}

JOB_PROFILES = {
    "Software Engineer": {
        "required": ["python","javascript","git","sql","rest api","docker"],
        "preferred": ["typescript","react","aws","kubernetes","ci/cd"],
        "keywords": ["software development","algorithms","data structures","oop","coding"]
    },
    "Data Scientist": {
        "required": ["python","sql","pandas","numpy","scikit-learn","machine learning"],
        "preferred": ["tensorflow","pytorch","spark","aws","tableau","deep learning"],
        "keywords": ["data analysis","statistics","modeling","visualization","insights"]
    },
    "Frontend Developer": {
        "required": ["javascript","react","html","css","git"],
        "preferred": ["typescript","vue","angular","webpack","figma","next.js"],
        "keywords": ["ui","ux","responsive","component","accessibility"]
    },
    "Backend Developer": {
        "required": ["python","node.js","sql","rest api","docker","git"],
        "preferred": ["postgresql","redis","kafka","kubernetes","aws","microservices"],
        "keywords": ["api","server","database","scalability","performance"]
    },
    "DevOps Engineer": {
        "required": ["docker","kubernetes","ci/cd","linux","git","aws"],
        "preferred": ["terraform","ansible","jenkins","prometheus","grafana"],
        "keywords": ["automation","deployment","infrastructure","monitoring","reliability"]
    },
    "ML Engineer": {
        "required": ["python","machine learning","tensorflow","pytorch","sql","git"],
        "preferred": ["mlflow","kubernetes","aws","spark","llm","deep learning"],
        "keywords": ["model training","deployment","pipeline","experimentation","optimization"]
    },
    "Full Stack Developer": {
        "required": ["javascript","react","node.js","sql","git","html","css"],
        "preferred": ["typescript","docker","aws","postgresql","redis"],
        "keywords": ["full stack","frontend","backend","api","database"]
    },
    "Product Manager": {
        "required": ["agile","scrum","jira","excel","sql"],
        "preferred": ["tableau","power bi","figma","confluence","python"],
        "keywords": ["product roadmap","stakeholder","requirements","kpi","strategy"]
    }
}

ATS_PATTERNS = {
    "contact_info": ["email","phone","linkedin","github","location","address"],
    "education": ["education","university","college","degree","bachelor","master","phd","gpa"],
    "experience": ["experience","work history","employment","intern","position","role","responsibility"],
    "achievements": ["achieved","improved","increased","reduced","led","managed","built","delivered","%","$"],
    "action_verbs": ["developed","designed","implemented","created","built","managed","led","architected","optimized","automated","collaborated","mentored"]
}

def extract_text_from_pdf(file_bytes):
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"Error reading DOCX: {e}"

def extract_skills(text):
    t = text.lower()
    return {cat: [s for s in skills if s in t] for cat, skills in TECH_SKILLS.items() if any(s in t for s in skills)}

def calculate_ats_score(text):
    t = text.lower()
    bd, total = {}, 0
    for label, key, max_pts in [
        ("Contact Information","contact_info",15),("Education","education",15),
        ("Work Experience","experience",20),("Achievements & Metrics","achievements",15)
    ]:
        found = sum(1 for p in ATS_PATTERNS[key] if p in t)
        s = min(max_pts, (found/len(ATS_PATTERNS[key]))*max_pts*1.3)
        bd[label] = {"score": round(s,1),"max": max_pts,"found": found,"total": len(ATS_PATTERNS[key])}
        total += s
    sf = sum(1 for skills in TECH_SKILLS.values() for s in skills if s in t)
    ss = min(20,(sf/10)*20)
    bd["Technical Skills"] = {"score": round(ss,1),"max": 20,"found": sf,"total": "10+ recommended"}
    total += ss
    vf = sum(1 for v in ATS_PATTERNS["action_verbs"] if v in t)
    vs = min(10,(vf/5)*10)
    bd["Action Verbs"] = {"score": round(vs,1),"max": 10,"found": vf,"total": "5+ recommended"}
    total += vs
    wc = len(text.split())
    ls = 5 if 400<=wc<=800 else (3 if wc>200 else 1)
    bd["Length & Format"] = {"score": ls,"max": 5,"found": f"{wc} words","total": "400-800 ideal"}
    total += ls
    return {"total": round(min(100,total)),"breakdown": bd,"word_count": wc}

def match_jobs(text):
    t = text.lower()
    matches = []
    for title, p in JOB_PROFILES.items():
        rm = sum(1 for s in p["required"] if s in t)
        pm = sum(1 for s in p["preferred"] if s in t)
        km = sum(1 for k in p["keywords"] if k in t)
        score = (rm/len(p["required"]))*60+(pm/len(p["preferred"]))*25+(km/len(p["keywords"]))*15
        matches.append({"title":title,"match_score":round(score),"required_matched":rm,
            "required_total":len(p["required"]),"preferred_matched":pm,"preferred_total":len(p["preferred"]),
            "missing_required":[s for s in p["required"] if s not in t][:4],
            "missing_preferred":[s for s in p["preferred"] if s not in t][:4]})
    return sorted(matches,key=lambda x:x["match_score"],reverse=True)[:5]

def query_llm(prompt, max_tokens=1500):
    try:
        r = requests.post(OLLAMA_URL,json={"model":MODEL_NAME,"prompt":prompt,"stream":False,
            "options":{"num_predict":max_tokens,"temperature":0.7}},timeout=120)
        return r.json().get("response","") if r.status_code==200 else None
    except:
        return None

def analyze_with_llm(resume_text):
    prompt = f"""You are an expert resume coach. Analyze this resume and respond with ONLY valid JSON.
RESUME: {resume_text[:3000]}
JSON: {{"overall_impression":"...","top_strengths":["..."],"critical_improvements":[{{"issue":"...","fix":"...","priority":"high"}}],"missing_sections":["..."],"linkedin_suggestions":{{"headline":"...","summary":"...","tips":["..."]}},"rewrite_bullets":[{{"original":"...","improved":"..."}}]}}"""
    result = query_llm(prompt)
    if result:
        try:
            m = re.search(r'\{.*\}', result, re.DOTALL)
            if m: return json.loads(m.group())
        except: pass
    return generate_fallback(resume_text)

def generate_fallback(text):
    t = text.lower()
    wc = len(text.split())
    improvements = []
    if "%" not in text: improvements.append({"issue":"No quantifiable achievements","fix":"Add metrics: increased X by Y%, saved $Z","priority":"high"})
    if "linkedin" not in t: improvements.append({"issue":"Missing LinkedIn URL","fix":"Add LinkedIn URL in contact section","priority":"high"})
    if "github" not in t: improvements.append({"issue":"No GitHub/portfolio link","fix":"Add GitHub URL to showcase projects","priority":"medium"})
    if wc < 300: improvements.append({"issue":"Resume too short","fix":"Expand with more details","priority":"high"})
    if "summary" not in t: improvements.append({"issue":"Missing professional summary","fix":"Add 2-3 sentence summary at top","priority":"medium"})
    return {
        "overall_impression": "Resume analyzed with local NLP. Focus on quantifiable achievements.",
        "top_strengths": ["Technical skills documented","Professional experience included","Educational background present"],
        "critical_improvements": improvements or [{"issue":"Generic bullets","fix":"Use action verbs with measurable outcomes","priority":"medium"}],
        "missing_sections": [s for s in ["Summary","Projects","Certifications"] if s.lower() not in t],
        "linkedin_suggestions": {
            "headline": "Software Engineer | Python · React · AWS | Building Scalable Solutions",
            "summary": "Results-driven engineer with expertise in full-stack development. Proven track record of delivering high-impact solutions. Seeking challenging opportunities.",
            "tips": ["Complete all profile sections (100% strength)","Add 3-5 featured projects","Request 3+ recommendations"]
        },
        "rewrite_bullets": [
            {"original":"Worked on backend","improved":"Architected RESTful APIs handling 50K+ daily requests, reducing latency by 35% via Redis caching"},
            {"original":"Helped with data analysis","improved":"Built Python ETL pipeline processing 1M+ daily records, enabling dashboards that drove 15% cost reduction"}
        ]
    }

@app.route("/api/analyze", methods=["POST"])
def analyze_resume():
    try:
        resume_text = ""
        if "file" in request.files:
            f = request.files["file"]
            fb, fn = f.read(), f.filename.lower()
            if fn.endswith(".pdf"): resume_text = extract_text_from_pdf(fb)
            elif fn.endswith(".docx"): resume_text = extract_text_from_docx(fb)
            elif fn.endswith(".txt"): resume_text = fb.decode("utf-8",errors="ignore")
            else: return jsonify({"error":"Use PDF, DOCX, or TXT"}),400
        elif request.json and "text" in request.json:
            resume_text = request.json["text"]
        else:
            return jsonify({"error":"No resume provided"}),400
        if not resume_text.strip():
            return jsonify({"error":"Could not extract text"}),400
        ats = calculate_ats_score(resume_text)
        skills = extract_skills(resume_text)
        jobs = match_jobs(resume_text)
        ai = analyze_with_llm(resume_text)
        top = jobs[0] if jobs else {}
        t = resume_text.lower()
        p = JOB_PROFILES.get(top.get("title","Software Engineer"),{"required":[],"preferred":[]})
        gap = {"target_role":top.get("title",""),"match_score":top.get("match_score",0),
               "have":[s for s in p["required"]+p["preferred"] if s in t],
               "missing_required":top.get("missing_required",[]),
               "missing_preferred":top.get("missing_preferred",[]),
               "learning_path":[f"Learn {s}" for s in top.get("missing_required",[])[:3]]}
        return jsonify({"success":True,"ats_score":ats,"skills":skills,"job_matches":jobs,"skill_gap":gap,"ai_analysis":ai})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/rewrite", methods=["POST"])
def rewrite():
    try:
        data = request.json
        text, role = data.get("text",""), data.get("target_role","Software Engineer")
        prompt = f"Rewrite this resume bullet for {role}. Start with action verb, add metrics. Return ONLY the improved text.\nOriginal: {text}"
        result = query_llm(prompt,200)
        return jsonify({"success":True,"rewritten":result.strip() if result else f"Engineered {role} solutions delivering measurable impact through cross-functional collaboration."})
    except Exception as e:
        return jsonify({"error":str(e)}),500

@app.route("/api/health", methods=["GET"])
def health():
    try:
        r = requests.get("http://localhost:11434/api/tags",timeout=3)
        models = [m["name"] for m in r.json().get("models",[])]
        return jsonify({"status":"ok","llm":any("llama" in m for m in models),"models":models})
    except:
        return jsonify({"status":"ok","llm":False,"models":[]})

if __name__ == "__main__":
    print("\n\u{1F9FE} AI Resume Analyzer Backend")
    print("=" * 40)
    print("Running on: http://localhost:5000")
    app.run(debug=True,port=5000,host="0.0.0.0")
