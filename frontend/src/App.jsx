import { useState, useRef, useEffect } from "react";
import { startInterview, submitAnswer, endEarly } from "./api";

// ── tiny helpers ──────────────────────────────────────────────────────────
function ScoreBadge({ score }) {
  if (score == null) return null;
  const cls =
    score >= 7
      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      : score >= 5
      ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
      : "bg-red-500/15 text-red-400 border-red-500/30";
  return (
    <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${cls}`}>
      {score}/10
    </span>
  );
}

function Spinner() {
  return (
    <div className="flex items-center gap-2 text-purple-400 text-sm">
      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      Processing…
    </div>
  );
}

// ── Setup stage ───────────────────────────────────────────────────────────
function SetupStage({ onStart }) {
  const [resumeMode, setResumeMode] = useState("text");
  const [resumeText, setResumeText] = useState("");
  const [resumePdf, setResumePdf] = useState(null);
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const canStart = jd.trim() && (resumeMode === "text" ? resumeText.trim() : resumePdf);

  async function handleStart() {
    setLoading(true);
    setError("");
    try {
      const data = await startInterview({ resumeText, resumePdf, jobDescription: jd });
      onStart(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto w-full px-4 py-12 flex flex-col gap-8">
      {/* hero */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 bg-purple-500/10 border border-purple-500/20 rounded-full px-4 py-1.5 text-purple-300 text-sm mb-4">
          🎯 AI Interview Coach
        </div>
        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">
          Ace your next interview
        </h1>
        <p className="text-slate-400 text-base">
          Resume-aware · Adaptive difficulty · Instant feedback
        </p>
      </div>

      {/* form card */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 flex flex-col gap-5 backdrop-blur">
        {/* resume toggle */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Resume</label>
          <div className="flex gap-2 mb-3">
            {["text", "pdf"].map((m) => (
              <button
                key={m}
                onClick={() => setResumeMode(m)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  resumeMode === m
                    ? "bg-purple-600 text-white"
                    : "bg-slate-800 text-slate-400 hover:text-white"
                }`}
              >
                {m === "text" ? "Paste text" : "Upload PDF"}
              </button>
            ))}
          </div>
          {resumeMode === "text" ? (
            <textarea
              rows={6}
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume here…"
              className="w-full bg-slate-800/70 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:border-purple-500/60 transition"
            />
          ) : (
            <label className="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-slate-700 rounded-xl cursor-pointer hover:border-purple-500/50 transition bg-slate-800/40">
              <span className="text-slate-400 text-sm">
                {resumePdf ? `✅ ${resumePdf.name}` : "Click to upload PDF"}
              </span>
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => setResumePdf(e.target.files[0])}
              />
            </label>
          )}
        </div>

        {/* JD */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">Job Description</label>
          <textarea
            rows={5}
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste the job description here…"
            className="w-full bg-slate-800/70 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:border-purple-500/60 transition"
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          disabled={!canStart || loading}
          onClick={handleStart}
          className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-sky-500 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
        >
          {loading ? "Analyzing resume…" : "Start Interview →"}
        </button>
      </div>

      {/* feature pills */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          ["📄", "Resume-aware", "Questions reference your actual projects"],
          ["📈", "Adaptive", "Difficulty adjusts to your performance"],
          ["🧾", "Full report", "Hiring recommendation + learning roadmap"],
        ].map(([icon, title, desc]) => (
          <div key={title} className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-white text-sm font-medium">{title}</div>
            <div className="text-slate-500 text-xs mt-1">{desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Interview stage ───────────────────────────────────────────────────────
function InterviewStage({ state, onAnswer, onEndEarly, loading }) {
  const { planner_info, history, current_question, current_topic, difficulty_level, asked_count } = state;
  const [answer, setAnswer] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, current_question]);

  function handleSubmit() {
    if (!answer.trim()) return;
    onAnswer(answer);
    setAnswer("");
  }

  const recColor = {
    "Strong Hire": "text-emerald-400",
    Hire: "text-sky-400",
    "No Hire": "text-amber-400",
    "Strong No Hire": "text-red-400",
  };

  return (
    <div className="max-w-2xl mx-auto w-full px-4 py-8 flex flex-col gap-6">
      {/* planner analysis — shown once */}
      {planner_info && (
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-5 backdrop-blur">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Resume ↔ JD Analysis</p>
          <div className="mb-2">
            <span className="text-xs text-slate-500 mr-2">Matched skills</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {planner_info.strengths.map((s) => (
                <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{s}</span>
              ))}
            </div>
          </div>
          <div>
            <span className="text-xs text-slate-500 mr-2">Gaps vs JD</span>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {planner_info.missing_skills.map((s) => (
                <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20">{s}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* progress bar */}
      <div className="flex items-center gap-3">
        <div className="flex-1 bg-slate-800 rounded-full h-1.5">
          <div
            className="bg-gradient-to-r from-purple-500 to-sky-400 h-1.5 rounded-full transition-all"
            style={{ width: `${Math.min((asked_count / 10) * 100, 100)}%` }}
          />
        </div>
        <span className="text-xs text-slate-400 whitespace-nowrap">Q {asked_count}/10</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20">
          {current_topic || "—"}
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
          ⚡ {difficulty_level}/5
        </span>
      </div>

      {/* Q&A history */}
      <div className="flex flex-col gap-4">
        {history.map((item, i) => (
          <div key={i} className="flex flex-col gap-2">
            <div className="bg-purple-500/8 border-l-2 border-purple-400 rounded-r-xl px-4 py-3">
              <p className="text-xs text-purple-300 font-medium mb-1">{item.topic}</p>
              <p className="text-sm text-slate-200">{item.question}</p>
            </div>
            <div className="bg-slate-800/50 border-l-2 border-sky-400 rounded-r-xl px-4 py-3">
              <p className="text-xs text-sky-300 font-medium mb-1 flex items-center gap-2">
                Your answer <ScoreBadge score={item.score} />
              </p>
              <p className="text-sm text-slate-300">{item.answer}</p>
            </div>
            <div className="bg-emerald-500/5 border border-emerald-500/15 rounded-xl px-4 py-2.5 text-xs text-emerald-300">
              💬 {item.feedback}
            </div>
          </div>
        ))}
      </div>

      {/* current question */}
      {current_question && (
        <div className="flex flex-col gap-3" ref={bottomRef}>
          <div className="bg-purple-500/8 border-l-2 border-purple-400 rounded-r-xl px-4 py-3">
            <p className="text-xs text-purple-300 font-medium mb-1">{current_topic}</p>
            <p className="text-sm text-slate-200">{current_question}</p>
          </div>
          <textarea
            rows={4}
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer here…"
            onKeyDown={(e) => e.key === "Enter" && e.ctrlKey && handleSubmit()}
            className="w-full bg-slate-800/70 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:border-purple-500/60 transition"
          />
          <div className="flex gap-2">
            <button
              disabled={!answer.trim() || loading}
              onClick={handleSubmit}
              className="flex-1 py-2.5 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-sky-500 hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-all text-sm"
            >
              {loading ? <span className="flex justify-center"><Spinner /></span> : "Submit answer →"}
            </button>
            <button
              onClick={onEndEarly}
              disabled={loading}
              className="px-4 py-2.5 rounded-xl text-sm font-medium text-red-400 border border-red-500/25 hover:bg-red-500/10 disabled:opacity-40 transition"
            >
              End early
            </button>
          </div>
          <p className="text-xs text-slate-600 text-center">Ctrl+Enter to submit</p>
        </div>
      )}

      {loading && !current_question && (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      )}
    </div>
  );
}

// ── Report stage ──────────────────────────────────────────────────────────
function ReportStage({ result, history, onRestart }) {
  const [showTranscript, setShowTranscript] = useState(false);

  const recColor = {
    "Strong Hire": "text-emerald-400",
    Hire: "text-sky-400",
    "No Hire": "text-amber-400",
    "Strong No Hire": "text-red-400",
  };

  return (
    <div className="max-w-2xl mx-auto w-full px-4 py-8 flex flex-col gap-6">
      {/* header card */}
      <div className="bg-gradient-to-br from-purple-500/15 to-sky-500/8 border border-purple-500/20 rounded-2xl p-6">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Final Assessment</p>
        <div className="flex gap-8 flex-wrap mb-4">
          <div>
            <p className="text-xs text-slate-500 mb-1">Overall Score</p>
            <p className="text-4xl font-bold text-white">{result.overall_score ?? "—"}<span className="text-lg text-slate-500">/10</span></p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Recommendation</p>
            <p className={`text-xl font-bold ${recColor[result.hiring_recommendation] ?? "text-purple-400"}`}>
              {result.hiring_recommendation ?? "—"}
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500 mb-1">Confidence</p>
            <p className="text-xl font-bold text-white">{result.confidence_level ?? "—"}</p>
          </div>
        </div>
        <p className="text-sm text-slate-300">{result.summary}</p>
      </div>

      {/* strengths / weaknesses */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
          <p className="text-sm font-semibold text-emerald-400 mb-2">✅ Strengths</p>
          <ul className="flex flex-col gap-1">
            {(result.strengths ?? []).map((s, i) => (
              <li key={i} className="text-xs text-slate-300">• {s}</li>
            ))}
          </ul>
        </div>
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
          <p className="text-sm font-semibold text-amber-400 mb-2">⚠️ Weaknesses</p>
          <ul className="flex flex-col gap-1">
            {(result.weaknesses ?? []).map((w, i) => (
              <li key={i} className="text-xs text-slate-300">• {w}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* impressive / weakest */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
          <p className="text-sm font-semibold text-sky-400 mb-2">🌟 Most Impressive</p>
          {(result.most_impressive_answers ?? []).map((a, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs font-medium text-white">{a.topic}</p>
              <p className="text-xs text-slate-400">{a.why}</p>
            </div>
          ))}
        </div>
        <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
          <p className="text-sm font-semibold text-red-400 mb-2">🩹 Weakest</p>
          {(result.weakest_answers ?? []).map((a, i) => (
            <div key={i} className="mb-2">
              <p className="text-xs font-medium text-white">{a.topic}</p>
              <p className="text-xs text-slate-400">{a.why}</p>
            </div>
          ))}
        </div>
      </div>

      {/* roadmap */}
      <div className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-4">
        <p className="text-sm font-semibold text-purple-400 mb-3">📚 Learning Roadmap</p>
        <div className="flex flex-col gap-2">
          {(result.recommended_learning_roadmap ?? []).map((r, i) => (
            <div key={i} className="flex gap-2 text-xs">
              <span className="text-white font-medium min-w-fit">{r.topic}:</span>
              <span className="text-slate-400">{r.resources}</span>
            </div>
          ))}
        </div>
      </div>

      {/* final feedback */}
      <div className="bg-sky-500/5 border border-sky-500/15 rounded-2xl p-4">
        <p className="text-sm font-semibold text-sky-400 mb-2">📝 Final Feedback</p>
        <p className="text-sm text-slate-300">{result.final_feedback}</p>
      </div>

      {/* transcript toggle */}
      <button
        onClick={() => setShowTranscript((v) => !v)}
        className="text-sm text-slate-400 hover:text-white transition underline underline-offset-2 text-left"
      >
        {showTranscript ? "Hide" : "Show"} full Q&A transcript
      </button>
      {showTranscript && (
        <div className="flex flex-col gap-4">
          {history.map((item, i) => (
            <div key={i} className="bg-slate-900/60 border border-slate-700/50 rounded-xl p-4 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-purple-300 font-medium">{item.topic}</span>
                <ScoreBadge score={item.score} />
              </div>
              <p className="text-xs text-slate-300"><span className="text-slate-500">Q: </span>{item.question}</p>
              <p className="text-xs text-slate-300"><span className="text-slate-500">A: </span>{item.answer}</p>
              <p className="text-xs text-slate-500 italic">{item.feedback}</p>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onRestart}
        className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-purple-600 to-sky-500 hover:opacity-90 transition-all"
      >
        🔄 Start New Interview
      </button>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────
export default function App() {
  const [stage, setStage] = useState("setup");
  const [interviewState, setInterviewState] = useState(null);
  const [loading, setLoading] = useState(false);

  function handleStart(data) {
    setInterviewState(data);
    setStage(data.stage);
  }

  async function handleAnswer(answer) {
    setLoading(true);
    try {
      const data = await submitAnswer({ threadId: interviewState.thread_id, answer });
      setInterviewState((prev) => ({ ...prev, ...data }));
      setStage(data.stage);
    } finally {
      setLoading(false);
    }
  }

  async function handleEndEarly() {
    setLoading(true);
    try {
      const data = await endEarly({ threadId: interviewState.thread_id });
      setInterviewState((prev) => ({ ...prev, ...data }));
      setStage("report");
    } finally {
      setLoading(false);
    }
  }

  function handleRestart() {
    setInterviewState(null);
    setStage("setup");
  }

  return (
    <div className="min-h-screen bg-[#0b0a14] text-slate-200">
      {stage === "setup" && <SetupStage onStart={handleStart} />}
      {stage === "interview" && (
        <InterviewStage
          state={interviewState}
          onAnswer={handleAnswer}
          onEndEarly={handleEndEarly}
          loading={loading}
        />
      )}
      {stage === "report" && (
        <ReportStage
          result={interviewState?.final_result ?? {}}
          history={interviewState?.history ?? []}
          onRestart={handleRestart}
        />
      )}
    </div>
  );
}
