// AI Resume Analyzer - Frontend Logic
const API_BASE = "http://localhost:5000";
let analysisData = null;

async function checkLLMStatus() {
    try {
        const r = await fetch(API_BASE + "/api/health", { signal: AbortSignal.timeout(3000) });
        const d = await r.json();
        const b = document.getElementById("llm-badge");
        if (d.llm) { b.textContent = "🟢 LLM Online"; b.className = "badge badge-online"; }
        else { b.textContent = "⭕ LLM Offline"; b.className = "badge badge-offline"; }
    } catch(e) {}
}

const dropZone = document.getElementById("drop-zone");
dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("dragover"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
dropZone.addEventListener("drop", (e) => { e.preventDefault(); dropZone.classList.remove("dragover"); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
document.getElementById("file-input").addEventListener("change", (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
    const ext = "." + file.name.split(".").pop().toLowerCase();
    if (![".pdf",".docx",".txt"].includes(ext)) { alert("Please upload a PDF, DOCX, or TXT file"); return; }
    const dc = dropZone.querySelector(".drop-zone-content");
    dc.innerHTML = "<span class=\"drop-icon\">✅</span><p><strong>" + file.name + "</strong></p><p class=\"drop-sub\">" + (file.size/1024).toFixed(1) + " KB - Ready</p>";
    window._file = file;
}

async function analyzeResume() {
    const txt = document.getElementById("resume-text").value.trim();
    const role = document.getElementById("target-role").value;
    const btn = document.getElementById("analyze-btn");
    if (!window._file && !txt) { alert("Please upload a resume or paste resume text."); return; }
    document.getElementById("upload-section").classList.add("hidden");
    document.getElementById("loading-section").classList.remove("hidden");
    btn.disabled = true;
    const steps = ["step-1","step-2","step-3","step-4","step-5"];
    let cur = 0;
    const iv = setInterval(() => {
        if (cur > 0) { document.getElementById(steps[cur-1]).classList.remove("active"); document.getElementById(steps[cur-1]).classList.add("done"); }
        if (cur < steps.length) { document.getElementById(steps[cur]).classList.add("active"); cur++; }
        else clearInterval(iv);
    }, 600);
    try {
        let resp;
        if (window._file) {
            const fd = new FormData();
            fd.append("file", window._file);
            fd.append("target_role", role);
            resp = await fetch(API_BASE + "/api/analyze", { method: "POST", body: fd });
        } else {
            resp = await fetch(API_BASE + "/api/analyze", {
                method: "POST", headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ text: txt, target_role: role })
            });
        }
        if (!resp.ok) throw new Error("Server error " + resp.status);
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        clearInterval(iv);
        steps.forEach(s => { document.getElementById(s).classList.remove("active"); document.getElementById(s).classList.add("done"); });
        analysisData = data;
        setTimeout(() => displayResults(data, role), 800);
    } catch(err) {
        clearInterval(iv);
        document.getElementById("loading-section").classList.add("hidden");
        document.getElementById("upload-section").classList.remove("hidden");
        btn.disabled = false;
        alert("Analysis failed: " + err.message + "\n\nStart the server: pip install -r requirements.txt && python app.py");
    }
}

function displayResults(data, role) {
    document.getElementById("loading-section").classList.add("hidden");
    document.getElementById("results-section").classList.remove("hidden");
    document.getElementById("resume-preview-name").textContent = (window._file ? window._file.name : "Pasted Resume") + " — " + role;
    const ats = data.ats_score;
    document.getElementById("ats-score-num").textContent = ats.total;
    const ring = document.getElementById("ats-ring");
    const offset = 326.7 - (ats.total / 100) * 326.7;
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 200);
    let col, grade;
    if (ats.total >= 80) { col = "#22c55e"; grade = "🟢 Excellent"; }
    else if (ats.total >= 60) { col = "#6366f1"; grade = "🔵 Good"; }
    else if (ats.total >= 40) { col = "#f59e0b"; grade = "🟡 Fair"; }
    else { col = "#ef4444"; grade = "🔴 Needs Work"; }
    ring.style.stroke = col;
    const g = document.getElementById("ats-grade");
    g.textContent = grade; g.style.color = col;
    const top = data.job_matches[0];
    document.getElementById("top-match-title").textContent = top.title;
    document.getElementById("top-match-pct").textContent = top.match_score + "% match";
    setTimeout(() => { document.getElementById("top-match-bar").style.width = top.match_score + "%"; }, 200);
    document.getElementById("ai-impression").textContent = data.ai_analysis.overall_impression;
    renderATSBreakdown(ats.breakdown);
    renderSkills(data.skills);
    renderJobMatches(data.job_matches);
    renderSkillGap(data.skill_gap);
    renderAIInsights(data.ai_analysis);
    renderLinkedIn(data.ai_analysis.linkedin_suggestions);
    renderRewrites(data.ai_analysis.rewrite_bullets);
    document.getElementById("results-section").scrollIntoView({ behavior: "smooth" });
}

function renderATSBreakdown(bd) {
    const c = document.getElementById("ats-breakdown");
    c.innerHTML = Object.entries(bd).map(([lbl, info]) => {
        const pct = (info.score / info.max) * 100;
        const fc = pct >= 75 ? "fill-good" : pct >= 45 ? "fill-ok" : "fill-bad";
        return "<div class=\"breakdown-item\"><div class=\"breakdown-header\"><span class=\"breakdown-label\">" + lbl + "</span><span class=\"breakdown-score\">" + info.score + "/" + info.max + "</span></div><div class=\"breakdown-bar\"><div class=\"breakdown-fill " + fc + "\" data-w=\"" + pct + "%\" style=\"width:0%\"></div></div><div class=\"breakdown-detail\">Found: " + info.found + " of " + info.total + "</div></div>";
    }).join("");
    setTimeout(() => c.querySelectorAll(".breakdown-fill").forEach(el => el.style.width = el.dataset.w), 100);
}

function renderSkills(skills) {
    const c = document.getElementById("skills-display");
    const em = {programming:"💻",web:"🌐",data:"📊",cloud:"☁️",ai_ml:"🤖",tools:"🛠️"};
    const nm = {programming:"Programming",web:"Web / Frontend",data:"Data & Databases",cloud:"Cloud & DevOps",ai_ml:"AI / ML",tools:"Tools & Methods"};
    if (!Object.keys(skills).length) { c.innerHTML = "<p class=\"no-skills\">No recognized technical skills found. Add specific technology names.</p>"; return; }
    c.innerHTML = Object.entries(skills).map(([cat, sl]) =>
        "<div class=\"skill-category\"><div class=\"category-title\">" + (em[cat]||"🔷") + " " + (nm[cat]||cat) + "</div><div class=\"skill-tags\">" + sl.map(s => "<span class=\"skill-tag\">" + s + "</span>").join("") + "</div></div>"
    ).join("");
}

function renderJobMatches(matches) {
    const c = document.getElementById("job-matches-display");
    c.innerHTML = matches.map((job, i) => {
        const md = i===0?"🥇":i===1?"🥈":i===2?"🥉":"▪";
        const miss = job.missing_required.length ? "<div class=\"job-missing\">Missing: " + job.missing_required.map(s => "<span class=\"missing-tag\">" + s + "</span>").join("") + "</div>" : "";
        return "<div class=\"job-match-item\"><div class=\"job-match-header\"><span class=\"job-title\">" + md + " " + job.title + "</span><span class=\"job-pct\">" + job.match_score + "%</span></div><div class=\"job-bar\"><div class=\"job-bar-fill\" data-w=\"" + job.match_score + "%\" style=\"width:0%\"></div></div><div class=\"job-details\"><span>✅ Required: " + job.required_matched + "/" + job.required_total + "</span><span>⭐ Preferred: " + job.preferred_matched + "/" + job.preferred_total + "</span></div>" + miss + "</div>";
    }).join("");
    setTimeout(() => c.querySelectorAll(".job-bar-fill").forEach(el => el.style.width = el.dataset.w), 100);
}

function renderSkillGap(gap) {
    const sh = document.getElementById("skills-have");
    sh.innerHTML = gap.have&&gap.have.length ? gap.have.map(s => "<span class=\"gap-tag have-tag\">✓ " + s + "</span>").join("") : "<p class=\"no-skills\">No matched skills for this role.</p>";
    const mr = document.getElementById("skills-missing-req");
    mr.innerHTML = gap.missing_required&&gap.missing_required.length ? gap.missing_required.map(s => "<span class=\"gap-tag req-tag\">✗ " + s + "</span>").join("") : "<p style=\"color:var(--success);font-size:14px\">✅ You have all required skills!</p>";
    const mp = document.getElementById("skills-missing-pref");
    mp.innerHTML = gap.missing_preferred&&gap.missing_preferred.length ? gap.missing_preferred.map(s => "<span class=\"gap-tag pref-tag\">○ " + s + "</span>").join("") : "<p style=\"color:var(--success);font-size:14px\">✅ All preferred skills covered!</p>";
    const lp = document.getElementById("learning-path");
    lp.innerHTML = gap.learning_path&&gap.learning_path.length ? gap.learning_path.map((s,i) => "<div class=\"learning-step\"><div class=\"step-num\">" + (i+1) + "</div><div class=\"step-content\">" + s + " — Search on YouTube, Udemy, or official docs</div></div>").join("") : "<p style=\"color:var(--success);font-size:14px\">🎉 No critical skill gaps for this role!</p>";
}

function renderAIInsights(ai) {
    document.getElementById("ai-strengths").innerHTML = (ai.top_strengths||[]).map(s =>
        "<div class=\"strength-item\"><span class=\"item-icon\">💪</span><span class=\"item-detail\">" + s + "</span></div>"
    ).join("");
    document.getElementById("ai-improvements").innerHTML = (ai.critical_improvements||[]).map(imp =>
        "<div class=\"improvement-item priority-" + (imp.priority||"medium") + "\"><span class=\"item-icon\">⚠️</span><div class=\"item-content\"><div class=\"item-title\">" + imp.issue + " <span class=\"priority-badge priority-" + imp.priority + "\">" + imp.priority + "</span></div><div class=\"item-detail\">" + imp.fix + "</div></div></div>"
    ).join("");
    const ms = ai.missing_sections||[];
    document.getElementById("ai-missing").innerHTML = ms.length ? ms.map(s => "<span class=\"missing-section-tag\">+ Add " + s + "</span>").join("") : "<span style=\"color:var(--success);font-size:14px\">✅ All key sections present!</span>";
}

function renderLinkedIn(li) {
    if (!li) return;
    document.getElementById("li-headline").textContent = li.headline||"";
    document.getElementById("li-summary").textContent = li.summary||"";
    document.getElementById("li-tips").innerHTML = (li.tips||[]).map(t => "<div class=\"li-tip\"><span>" + t + "</span></div>").join("");
}

function renderRewrites(bullets) {
    const c = document.getElementById("ai-rewrites");
    if (!bullets||!bullets.length) { c.innerHTML = "<p style=\"color:var(--text3)\">No rewrite examples available.</p>"; return; }
    c.innerHTML = bullets.map(b =>
        "<div class=\"rewrite-example\"><div class=\"before-after\"><div><div class=\"before-label\">Before</div><div class=\"before-text\">" + b.original + "</div></div><div><div class=\"after-label\">After (AI Improved)</div><div class=\"after-text\">" + b.improved + "</div></div></div></div>"
    ).join("");
}

async function rewriteBullet(btn) {
    const text = document.getElementById("bullet-input").value.trim();
    const role = document.getElementById("rewrite-role").value;
    if (!text) { alert("Please enter a bullet point."); return; }
    const orig = btn.innerHTML;
    btn.textContent = "⏳ Rewriting..."; btn.disabled = true;
    try {
        const r = await fetch(API_BASE + "/api/rewrite", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({text, target_role: role}) });
        const d = await r.json();
        if (d.rewritten) {
            document.getElementById("rewrite-output").textContent = d.rewritten;
            document.getElementById("rewrite-result").classList.remove("hidden");
        }
    } catch(e) { alert("Rewrite failed. Make sure the server is running."); }
    btn.innerHTML = orig; btn.disabled = false;
}

function copyRewrite() {
    navigator.clipboard.writeText(document.getElementById("rewrite-output").textContent).then(() => {
        event.target.textContent = "✅ Copied!";
        setTimeout(() => event.target.textContent = "📋 Copy", 1500);
    });
}

function showTab(name, btn) {
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.getElementById("tab-" + name).classList.add("active");
    btn.classList.add("active");
}

function resetAnalysis() {
    document.getElementById("results-section").classList.add("hidden");
    document.getElementById("upload-section").classList.remove("hidden");
    document.getElementById("analyze-btn").disabled = false;
    window._file = null;
    document.getElementById("resume-text").value = "";
    const dc = dropZone.querySelector(".drop-zone-content");
    dc.innerHTML = "<span class=\"drop-icon\">⬆️</span><p><strong>Drag and drop your resume here</strong></p><p class=\"drop-sub\">or click to browse files</p><p class=\"drop-formats\">PDF, DOCX, TXT supported</p>";
    window.scrollTo({top: 0, behavior: "smooth"});
}

checkLLMStatus();
