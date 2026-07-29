"""
AI Interview Coach — Streamlit UI
----------------------------------
Frontend for the LangGraph interview agent defined in `workflow/agent.py`.
Mirrors the terminal runner (`run_interview.py`): streams the graph with
stream_mode="updates", surfaces planner analysis, per-answer scoring, and
supports ending the interview early (pulls whatever's in the checkpointer
and runs `final_evaluation_node` directly, same as the CLI's early-exit path).

SETUP
1. Keep this file at your project root, next to the `workflow/` and
   `helper/` packages (same layout as run_interview.py).
2. pip install -r requirements.txt
3. Put your MISTRAL_API_KEY in a `.env` file at the project root.
4. Run:  streamlit run streamlit_app.py
"""

import uuid
import streamlit as st
from langgraph.types import Command

# ── import the compiled graph + helper from your agent module ──────────────
try:
    from interview_agent import app as interview_app, final_evaluation_node
except ImportError:
    interview_app = None
    final_evaluation_node = None

try:
    from PdfLoader import load_pdf
except ImportError:
    load_pdf = None


# ─────────────────────────────────────────────────────────────────────────
# PAGE CONFIG + STYLING
# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }

.stApp {
    background: radial-gradient(circle at 10% 0%, #1b1035 0%, #0b0a19 45%, #060512 100%);
    color: #eae7f6;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #150f2e 0%, #0c0a1c 100%);
    border-right: 1px solid rgba(154, 118, 255, 0.15);
}

.hero {
    padding: 2.4rem 2.2rem;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(124,58,237,0.25), rgba(56,189,248,0.12));
    border: 1px solid rgba(168, 130, 255, 0.25);
    margin-bottom: 1.6rem;
}
.hero h1 {
    font-size: 2.4rem;
    margin: 0 0 0.4rem 0;
    background: linear-gradient(90deg, #b794ff, #7dd3fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero p { color: #b9b3d6; font-size: 1.02rem; margin: 0; }

.badge {
    display: inline-block;
    padding: 0.22rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    margin-right: 0.4rem;
}
.badge-topic { background: rgba(56,189,248,0.15); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.35);}
.badge-diff  { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.35);}
.badge-score-high { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.35);}
.badge-score-mid  { background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.35);}
.badge-score-low  { background: rgba(248,113,113,0.15); color: #f87171; border: 1px solid rgba(248,113,113,0.35);}
.badge-skill-have { background: rgba(74,222,128,0.12); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); margin-bottom: 0.3rem;}
.badge-skill-gap  { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.3); margin-bottom: 0.3rem;}

.q-card, .a-card {
    padding: 1.1rem 1.3rem;
    border-radius: 16px;
    margin-bottom: 0.7rem;
    border: 1px solid rgba(255,255,255,0.06);
}
.q-card { background: rgba(124,58,237,0.10); border-left: 3px solid #a78bfa; }
.a-card { background: rgba(255,255,255,0.03); border-left: 3px solid #38bdf8; }
.fb-card { background: rgba(74,222,128,0.05); border-left: 3px solid #4ade80; padding: 0.8rem 1.1rem; border-radius: 14px; font-size: 0.92rem; color: #cdeedb;}

.analysis-card {
    padding: 1.1rem 1.3rem;
    border-radius: 16px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 1rem;
}

.report-card {
    padding: 1.4rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(124,58,237,0.16), rgba(56,189,248,0.06));
    border: 1px solid rgba(168,130,255,0.25);
    margin-bottom: 1rem;
}

div.stButton > button {
    background: linear-gradient(90deg, #7c3aed, #38bdf8);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
    transition: 0.15s ease-in-out;
}
div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(124,58,237,0.4);
}
button[kind="secondary"] {
    background: rgba(248,113,113,0.12) !important;
    color: #f87171 !important;
    border: 1px solid rgba(248,113,113,0.35) !important;
}

hr { border-color: rgba(255,255,255,0.08); }
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────
defaults = {
    "stage": "setup",          # setup -> interview -> report
    "thread_id": str(uuid.uuid4()),
    "config": None,
    "current_question": None,
    "history": [],             # list of {topic, question, answer, score, feedback}
    "final_result": None,
    "state_snapshot": {},
    "planner_info": None,      # {missing_skills, strengths} from the planner node
    "pending_answer_key": 0,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)


def score_badge(score) -> str:
    if score is None:
        return ""
    cls = "badge-score-high" if score >= 7 else "badge-score-mid" if score >= 5 else "badge-score-low"
    return f'<span class="badge {cls}">Score: {score}/10</span>'


# ─────────────────────────────────────────────────────────────────────────
# GRAPH DRIVER — mirrors run_interview.py's event handling exactly:
# streams with stream_mode="updates", reacts to "planner", "final_evaluation",
# and "__interrupt__" events, then syncs from the checkpointer's live state.
# ─────────────────────────────────────────────────────────────────────────
def run_step(payload):
    final_report = None
    interrupted = False
    interrupt_question = None

    for event in interview_app.stream(payload, config=st.session_state.config, stream_mode="updates"):
        for node, data in event.items():
            if node == "planner":
                st.session_state.planner_info = {
                    "missing_skills": data.get("missing_skills", []),
                    "strengths": data.get("strengths", []),
                }
            elif node == "final_evaluation":
                final_report = data.get("final_result", {})
            elif node == "__interrupt__":
                interrupt_obj = data[0]
                value = interrupt_obj.value if hasattr(interrupt_obj, "value") else interrupt_obj
                interrupt_question = value.get("current_question", "")
                interrupted = True

    # pull the live, accumulated state (topic, difficulty, full Q&A history)
    snapshot = interview_app.get_state(st.session_state.config)
    values = snapshot.values
    st.session_state.state_snapshot = values
    st.session_state.history = values.get("interview_results", [])

    if final_report:
        st.session_state.final_result = final_report
        st.session_state.current_question = None
        st.session_state.stage = "report"
    elif interrupted:
        st.session_state.current_question = interrupt_question
        st.session_state.stage = "interview"
    else:
        st.session_state.current_question = None


def trigger_early_final():
    """Same as run_interview.py's _trigger_early_final: pull whatever's in the
    checkpointer and generate a report from the answers collected so far."""
    snapshot = interview_app.get_state(st.session_state.config)
    current_state = snapshot.values
    if not current_state.get("interview_results"):
        st.warning("No answers recorded yet — nothing to report on.")
        return
    report_state = final_evaluation_node(current_state)
    st.session_state.final_result = report_state["final_result"]
    st.session_state.history = current_state.get("interview_results", [])
    st.session_state.current_question = None
    st.session_state.stage = "report"


# ─────────────────────────────────────────────────────────────────────────
# SIDEBAR — SETUP
# ─────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Interview Setup")

    resume_mode = st.radio("Resume input", ["Paste text", "Upload PDF"], horizontal=True)
    resume_text = ""
    if resume_mode == "Paste text":
        resume_text = st.text_area("Resume", height=180, placeholder="Paste resume text here…")
    else:
        pdf_file = st.file_uploader("Upload resume PDF", type=["pdf"])
        if pdf_file and load_pdf:
            with open("temp_resume.pdf", "wb") as f:
                f.write(pdf_file.read())
            resume_text = load_pdf("temp_resume.pdf")
            st.success("Resume loaded from PDF ✅")
        elif pdf_file and not load_pdf:
            st.error("helper.PdfLoader not found — paste resume text instead.")

    jd_text = st.text_area("Job Description", height=160, placeholder="Paste the job description here…")

    st.markdown("---")
    start_disabled = interview_app is None or not resume_text.strip() or not jd_text.strip()
    if interview_app is None:
        st.error("Couldn't import `app` from workflow/agent.py — make sure this file sits at the project root, next to the `workflow/` package.")

    if st.button("🚀 Start Interview", disabled=start_disabled, use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.config = {"configurable": {"thread_id": st.session_state.thread_id}}
        st.session_state.history = []
        st.session_state.final_result = None
        st.session_state.planner_info = None
        initial_state = {
            "resume": resume_text,
            "job_description": jd_text,
            "resume_projects": [],
            "interview_results": [],
            "skills_covered": [],
            "missing_skills": [],
            "strengths": [],
            "asked_questions": [],
            "covered_topics": [],
            "weak_topics": [],
            "strong_topics": [],
            "candidate_claims": [],
            "current_question": "",
            "current_answer": "",
            "current_topic": "",
            "current_result": {},
            "score": 0,
            "difficulty_level": 1,
            "follow_up_mode": False,
            "final_result": {},
        }
        with st.spinner("Analyzing resume & job description…"):
            run_step(initial_state)
        st.rerun()

    if st.session_state.stage == "interview":
        st.markdown("---")
        if st.button("🛑 End Interview Now", use_container_width=True, type="secondary"):
            with st.spinner("Generating your report from answers so far…"):
                trigger_early_final()
            st.rerun()

    if st.session_state.stage != "setup":
        st.markdown("---")
        if st.button("🔄 Restart", use_container_width=True):
            st.session_state.stage = "setup"
            st.session_state.config = None
            st.session_state.current_question = None
            st.session_state.history = []
            st.session_state.final_result = None
            st.session_state.state_snapshot = {}
            st.session_state.planner_info = None
            st.session_state.pending_answer_key = 0
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────
# MAIN — HERO
# ─────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
    <h1>🎯 AI Interview Coach</h1>
    <p>A resume-aware, difficulty-adaptive mock interviewer powered by LangGraph. Paste your resume and the job
    description on the left, then answer questions as they come — difficulty adjusts to how you're doing, and you
    can end early for a report on whatever you've answered so far.</p>
</div>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────
# STAGE: SETUP (idle)
# ─────────────────────────────────────────────────────────────────────────
if st.session_state.stage == "setup":
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### 📄 Resume-aware")
        st.write("Questions reference your actual projects and tech stack, not generic trivia.")
    with c2:
        st.markdown("#### 📈 Adaptive difficulty")
        st.write("Nail an answer and it gets harder. Struggle and it eases up — just like a real interview.")
    with c3:
        st.markdown("#### 🧾 Full report")
        st.write("Get a hiring recommendation, strengths, weaknesses, and a learning roadmap — anytime, even if you end early.")


# ─────────────────────────────────────────────────────────────────────────
# STAGE: INTERVIEW (Q&A loop)
# ─────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "interview":
    # planner analysis, shown once (mirrors the CLI's "Missing Skills / Strengths" print)
    if st.session_state.planner_info:
        pi = st.session_state.planner_info
        missing_html = "".join(f'<span class="badge badge-skill-gap">{s}</span>' for s in pi["missing_skills"]) or "None"
        strengths_html = "".join(f'<span class="badge badge-skill-have">{s}</span>' for s in pi["strengths"]) or "None"
        st.markdown(
            f"""
<div class="analysis-card">
    <b>📄 Resume ↔ JD Analysis</b><br><br>
    <span style="color:#b9b3d6;">Matched strengths</span><br>{strengths_html}<br><br>
    <span style="color:#b9b3d6;">Gaps vs. job description</span><br>{missing_html}
</div>
""",
            unsafe_allow_html=True,
        )

    snap = st.session_state.state_snapshot
    topic = snap.get("current_topic", "—")
    difficulty = snap.get("difficulty_level", 1)
    asked_count = len(snap.get("asked_questions", []))

    prog_col, meta_col = st.columns([3, 1])
    with prog_col:
        st.progress(min(asked_count / 10, 1.0), text=f"Question {asked_count} of ~10")
    with meta_col:
        st.markdown(
            f'<span class="badge badge-topic">📌 {topic}</span>'
            f'<span class="badge badge-diff">⚡ Difficulty {difficulty}/5</span>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # past Q&A
    for item in st.session_state.history:
        st.markdown(f'<div class="q-card"><b>Q · {item["topic"]}</b><br>{item["question"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="a-card"><b>Your answer</b><br>{item["answer"]}</div>', unsafe_allow_html=True)
        st.markdown(score_badge(item["score"]), unsafe_allow_html=True)
        st.markdown(f'<div class="fb-card">💬 {item["feedback"]}</div>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    # current question
    if st.session_state.current_question:
        st.markdown(
            f'<div class="q-card"><b>Q · {topic}</b><br>{st.session_state.current_question}</div>',
            unsafe_allow_html=True,
        )
        answer_key = f"answer_input_{st.session_state.pending_answer_key}"
        answer = st.text_area("Your answer", key=answer_key, height=140, label_visibility="collapsed",
                               placeholder="Type your answer here…")
        submit = st.button("Submit answer ➜", use_container_width=True)
        if submit and answer.strip():
            with st.spinner("Evaluating your answer…"):
                run_step(Command(resume=answer))
            st.session_state.pending_answer_key += 1
            st.rerun()
        elif submit:
            st.warning("Please write an answer before submitting.")


# ─────────────────────────────────────────────────────────────────────────
# STAGE: REPORT
# ─────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "report":
    result = st.session_state.final_result or {}

    rec = result.get("hiring_recommendation", "—")
    rec_color = {
        "Strong Hire": "#4ade80", "Hire": "#7dd3fc",
        "No Hire": "#fbbf24", "Strong No Hire": "#f87171",
    }.get(rec, "#a78bfa")

    st.markdown(
        f"""
<div class="report-card">
    <h2 style="margin-top:0;">🏁 Final Assessment</h2>
    <div style="display:flex; gap:2.2rem; align-items:center; flex-wrap: wrap;">
        <div>
            <div style="font-size:0.85rem; color:#b9b3d6;">Overall Score</div>
            <div style="font-size:2.4rem; font-weight:700;">{result.get("overall_score", "—")}/10</div>
        </div>
        <div>
            <div style="font-size:0.85rem; color:#b9b3d6;">Recommendation</div>
            <div style="font-size:1.4rem; font-weight:700; color:{rec_color};">{rec}</div>
        </div>
        <div>
            <div style="font-size:0.85rem; color:#b9b3d6;">Confidence</div>
            <div style="font-size:1.4rem; font-weight:700;">{result.get("confidence_level", "—")}</div>
        </div>
    </div>
    <p style="margin-top:1rem; color:#dcd8f0;">{result.get("summary", "")}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ✅ Strengths")
        for s in result.get("strengths", []):
            st.markdown(f"- {s}")
    with c2:
        st.markdown("#### ⚠️ Weaknesses")
        for w in result.get("weaknesses", []):
            st.markdown(f"- {w}")

    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### 🌟 Most Impressive Answers")
        for a in result.get("most_impressive_answers", []):
            st.markdown(f"**{a.get('topic','')}** — {a.get('question','')}")
            st.caption(a.get("why", ""))
    with c4:
        st.markdown("#### 🩹 Weakest Answers")
        for a in result.get("weakest_answers", []):
            st.markdown(f"**{a.get('topic','')}** — {a.get('question','')}")
            st.caption(a.get("why", ""))

    st.markdown("---")
    st.markdown("#### 📚 Recommended Learning Roadmap")
    for r in result.get("recommended_learning_roadmap", []):
        st.markdown(f"**{r.get('topic','')}**: {r.get('resources','')}")

    st.markdown("---")
    st.markdown("#### 📝 Final Feedback")
    st.info(result.get("final_feedback", ""))

    with st.expander("📋 Full Q&A Transcript"):
        for item in st.session_state.history:
            st.markdown(f"**{item['topic']}** — {score_badge(item['score'])}", unsafe_allow_html=True)
            st.markdown(f"Q: {item['question']}")
            st.markdown(f"A: {item['answer']}")
            st.markdown(f"_{item['feedback']}_")
            st.markdown("---")