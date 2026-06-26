"""
Prompt Doctor 2.0 — The Prompt Engineering Challenge
Gamified prompt engineering training platform with auto-progression.
"""

import json
import os
import time
import streamlit as st
from levels import get_level, get_domains
from examiner import grade_prompt

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Prompt Doctor — The Prompt Engineering Challenge",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Dark Theme CSS
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #E2E8F0 !important; }
    .stApp { background: #0F172A; }
    .main > div { padding: 0 2rem; }
    p, li, span, div, label, .stMarkdown, .stText { color: #E2E8F0; }
    h1, h2, h3, h4, h5, h6, strong { color: #F1F5F9 !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }

    .app-title { font-size: 1.6rem; font-weight: 800; color: #F1F5F9; letter-spacing: -0.03em; margin: 0; line-height: 1.2; }
    .app-subtitle { font-size: 0.8rem; color: #94A3B8; margin: 0; }
    .section-title { font-size: 1rem; font-weight: 600; color: #F1F5F9; margin: 0.8rem 0 0.6rem 0; letter-spacing: -0.01em; }

    .glass-card {
        background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(20px);
        border: 1px solid rgba(71, 85, 105, 0.4); border-radius: 14px;
        padding: 1.2rem; box-shadow: 0 1px 3px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.25s ease; margin-bottom: 0.8rem;
    }

    .level-card {
        background: rgba(30, 41, 59, 0.85); backdrop-filter: blur(20px);
        border: 2px solid rgba(71, 85, 105, 0.5); border-radius: 12px;
        padding: 0.8rem 1.2rem; cursor: pointer;
        transition: all 0.3s ease; margin-bottom: 0.4rem;
    }
    .level-card:hover { transform: translateX(3px); border-color: #60A5FA; }
    .level-card.active { border-color: #60A5FA; box-shadow: 0 0 0 3px rgba(96,165,250,0.2); }
    .level-card.passed { border-color: #22C55E; background: rgba(34,197,94,0.08); }
    .level-card.locked { opacity: 0.35; cursor: not-allowed; filter: grayscale(0.5); }
    .level-card.failed { border-color: #EF4444; background: rgba(239,68,68,0.08); }
    .level-icon { font-size: 1.3rem; margin-right: 0.6rem; display: inline-block; vertical-align: middle; }
    .level-name { font-size: 0.85rem; font-weight: 600; color: #F1F5F9; display: inline-block; vertical-align: middle; }
    .level-badge {
        display: inline-block; padding: 0.1rem 0.5rem; border-radius: 20px;
        font-size: 0.6rem; font-weight: 600; text-transform: uppercase;
        letter-spacing: 0.04em; vertical-align: middle; margin-left: 0.4rem;
    }
    .level-badge.passed-badge { background: rgba(34,197,94,0.15); color: #22C55E; border: 1px solid rgba(34,197,94,0.3); }
    .level-badge.active-badge { background: rgba(96,165,250,0.15); color: #60A5FA; border: 1px solid rgba(96,165,250,0.3); }
    .level-badge.locked-badge { background: #1E293B; color: #64748B; border: 1px solid #334155; }
    .level-badge.failed-badge { background: rgba(239,68,68,0.15); color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }

    .stTextArea textarea {
        border: 2px solid #334155 !important; border-radius: 12px !important;
        font-size: 0.9rem !important; line-height: 1.6 !important;
        padding: 1rem !important; font-family: 'Inter', sans-serif !important;
        background: #1E293B !important; color: #F1F5F9 !important;
        caret-color: #60A5FA !important;
    }
    .stTextArea textarea::placeholder { color: #64748B !important; opacity: 0.7; }
    .stTextArea textarea:focus { border-color: #60A5FA !important; box-shadow: 0 0 0 3px rgba(96,165,250,0.15) !important; }

    .stButton button {
        border-radius: 10px !important; font-weight: 600 !important;
        font-size: 0.85rem !important; padding: 0.4rem 1.2rem !important;
        transition: all 0.2s ease !important; border: none !important;
        color: #F1F5F9 !important;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
        box-shadow: 0 2px 8px rgba(59,130,246,0.3) !important;
    }
    .stButton button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(59,130,246,0.4) !important;
    }

    .stSelectbox [data-baseweb="select"] {
        border-radius: 10px !important; border: 2px solid #334155 !important;
        background: #1E293B !important;
    }
    .stSelectbox [data-baseweb="select"] > div { background: #1E293B !important; color: #F1F5F9 !important; }

    .verdict-pass { display: inline-flex; align-items: center; gap: 0.4rem; background: linear-gradient(135deg, #22C55E, #16A34A); color: #F1F5F9; font-weight: 700; font-size: 0.9rem; padding: 0.3rem 1rem; border-radius: 30px; box-shadow: 0 2px 8px rgba(34,197,94,0.3); }
    .verdict-revise { display: inline-flex; align-items: center; gap: 0.4rem; background: linear-gradient(135deg, #EF4444, #DC2626); color: #F1F5F9; font-weight: 700; font-size: 0.9rem; padding: 0.3rem 1rem; border-radius: 30px; box-shadow: 0 2px 8px rgba(239,68,68,0.3); }

    .criterion-item { border-radius: 8px; padding: 0.5rem 0.8rem; margin-bottom: 0.4rem; font-size: 0.82rem; }
    .criterion-pass { background: rgba(34,197,94,0.08); border: 1px solid rgba(34,197,94,0.25); }
    .criterion-fail { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); }
    .criterion-name { font-weight: 600; font-size: 0.82rem; color: #F1F5F9; margin-bottom: 0.1rem; }
    .criterion-status-pass { font-size: 0.7rem; color: #22C55E; }
    .criterion-status-fail { font-size: 0.7rem; color: #EF4444; }

    .line-analysis-item {
        background: rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem; border-left: 3px solid #60A5FA;
    }
    .line-phrase { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #FCA5A5; background: rgba(239,68,68,0.1); padding: 0.15rem 0.4rem; border-radius: 4px; }
    .line-issue { font-size: 0.78rem; color: #FCA5A5; margin-top: 0.2rem; }
    .line-why { font-size: 0.72rem; color: #94A3B8; margin-top: 0.15rem; }
    .line-question { font-size: 0.75rem; color: #93C5FD; margin-top: 0.2rem; padding: 0.2rem 0.4rem; background: rgba(96,165,250,0.08); border-radius: 4px; border-left: 2px solid #60A5FA; }

    .custom-divider { border: none; height: 1px; background: linear-gradient(90deg, transparent, #334155, transparent); margin: 0.8rem 0; }

    .progress-container { display: flex; align-items: center; gap: 0.8rem; margin: 0.3rem 0; }
    .progress-bar-track { flex: 1; height: 6px; background: #334155; border-radius: 10px; overflow: hidden; }
    .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #3B82F6, #2563EB); border-radius: 10px; transition: width 0.6s cubic-bezier(0.4,0,0.2,1); }
    .progress-text { font-size: 0.75rem; font-weight: 600; color: #94A3B8; white-space: nowrap; }

    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; margin: 0.5rem 0; }
    .stat-card { background: rgba(30,41,59,0.7); border: 1px solid #334155; border-radius: 8px; padding: 0.5rem; text-align: center; }
    .stat-value { font-size: 1.1rem; font-weight: 700; color: #F1F5F9; }
    .stat-label { font-size: 0.6rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; }

    .xp-display { display: inline-flex; align-items: center; gap: 0.3rem; background: linear-gradient(135deg, #F59E0B, #D97706); color: #F1F5F9; font-weight: 700; font-size: 0.75rem; padding: 0.2rem 0.7rem; border-radius: 20px; }

    .understanding-box { background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.25); border-radius: 8px; padding: 0.6rem 0.8rem; font-size: 0.8rem; color: #93C5FD; margin-bottom: 0.6rem; }
    .feedback-box { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.25); border-radius: 8px; padding: 0.6rem 0.8rem; font-size: 0.8rem; color: #FDE68A; margin-bottom: 0.6rem; }
    .info-banner { background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.3); border-radius: 8px; padding: 0.5rem 0.8rem; font-size: 0.75rem; color: #FDE68A; margin-bottom: 0.6rem; }

    .json-box { background: #0F172A; color: #E2E8F0; padding: 0.8rem; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; line-height: 1.4; overflow-x: auto; white-space: pre-wrap; max-height: 300px; overflow-y: auto; border: 1px solid #334155; }
    .right-panel { background: rgba(30,41,59,0.4); border-radius: 14px; padding: 0.5rem 1.2rem 1.2rem 1.2rem; min-height: 400px; border: 1px solid rgba(71,85,105,0.3); }

    .empty-state { text-align: center; padding: 2rem 1rem; color: #64748B; }
    .empty-state-icon { font-size: 2.5rem; margin-bottom: 0.5rem; }
    .empty-state-title { font-size: 0.9rem; font-weight: 600; color: #94A3B8; margin-bottom: 0.2rem; }
    .empty-state-desc { font-size: 0.75rem; line-height: 1.5; color: #64748B; }

    @keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    .fade-in { animation: fadeInUp 0.4s ease forwards; }
    @keyframes confetti-fall { 0% { transform: translateY(-10px) rotate(0deg); opacity: 1; } 100% { transform: translateY(100vh) rotate(720deg); opacity: 0; } }
    @keyframes popIn { 0% { transform: scale(0.5); opacity: 0; } 70% { transform: scale(1.1); } 100% { transform: scale(1); opacity: 1; } }
    @keyframes pulseGlow { 0%, 100% { box-shadow: 0 0 20px rgba(96,165,250,0.3); } 50% { box-shadow: 0 0 40px rgba(96,165,250,0.6); } }

    .celebration-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(15, 23, 42, 0.85); z-index: 9997;
        display: flex; align-items: center; justify-content: center;
        animation: fadeInUp 0.3s ease;
    }
    .celebration-modal {
        background: rgba(30, 41, 59, 0.98); backdrop-filter: blur(30px);
        border: 2px solid #60A5FA; border-radius: 24px;
        padding: 2.5rem 3rem; text-align: center;
        animation: popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        box-shadow: 0 24px 80px rgba(0,0,0,0.5);
        max-width: 440px; width: 90%;
    }
    .celebration-modal.grand { border-color: #F59E0B; animation: pulseGlow 2s infinite, popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1); }
    .celebration-icon { font-size: 3.5rem; margin-bottom: 0.5rem; }
    .celebration-title { font-size: 1.4rem; font-weight: 800; color: #F1F5F9; margin-bottom: 0.3rem; }
    .celebration-subtitle { font-size: 0.85rem; color: #94A3B8; margin-bottom: 0.5rem; }
    .celebration-xp { font-size: 1.1rem; font-weight: 700; color: #F59E0B; }
    .confetti-piece { position: fixed; width: 8px; height: 8px; border-radius: 2px; z-index: 9998; animation: confetti-fall 2.5s ease-in forwards; pointer-events: none; }

    .stAlert { background: #1E293B !important; color: #E2E8F0 !important; border: 1px solid #334155 !important; }
    .stExpander { background: #1E293B !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
    .stExpander summary { color: #E2E8F0 !important; }
    .stCaption { color: #64748B !important; }
    .stTextInput input { background: #1E293B !important; color: #F1F5F9 !important; border: 2px solid #334155 !important; border-radius: 10px !important; }
    .stSpinner > div { border-color: #60A5FA !important; border-top-color: transparent !important; }
    .strength-meter { height: 4px; border-radius: 4px; background: #334155; overflow: hidden; margin: 0.3rem 0; }
    .strength-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------

def init_session_state():
    defaults = {
        "auto_result": None,
        "evaluating": False,
        "error_message": None,
        "submission_count": 0,
        "show_celebration": False,
        "celebration_data": None,
        "show_victory": False,
        "victory_data": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LEVEL_XP = {1: 100, 2: 200, 3: 350, 4: 500, 5: 750}
LEVEL_ICONS = {1: "🌱", 2: "📋", 3: "🧩", 4: "🧠", 5: "🏆"}
LEVEL_NAMES = {1: "Basic Prompt", 2: "Structured Output", 3: "Few-Shot Learning", 4: "Reasoning", 5: "Robustness"}

CELEBRATION_MESSAGES = {
    1: {"title": "🌱 Level 1 Cleared!", "subtitle": "Role & Instruction Mastered", "color": "#22C55E"},
    2: {"title": "📋 Level 2 Cleared!", "subtitle": "Structured Output Unlocked", "color": "#60A5FA"},
    3: {"title": "🧩 Level 3 Cleared!", "subtitle": "Few-Shot Expert", "color": "#A78BFA"},
    4: {"title": "🧠 Level 4 Cleared!", "subtitle": "Reasoning Master", "color": "#F9A8D4"},
    5: {"title": "🏆 Level 5 Cleared!", "subtitle": "Prompt Engineering Champion", "color": "#F59E0B"},
}

# ---------------------------------------------------------------------------
# Auto-Progression Engine (inline to avoid import issues)
# ---------------------------------------------------------------------------

def evaluate_auto(
    user_prompt: str,
    start_level: int = 1,
    domain: str = "general",
    api_key: str = None,
    model: str = "deepseek/deepseek-r1:free",
) -> dict:
    """
    Evaluate a prompt through progressive levels.
    Stops at the first failure or completes all 5 levels.
    """
    if not user_prompt or not user_prompt.strip():
        return {
            "error": True,
            "message": "Prompt cannot be empty.",
            "levels": [],
            "passed_levels": [],
            "failed_at": None,
            "all_passed": False,
            "total_passed": 0,
            "total_xp": 0,
            "completion_pct": 0,
        }

    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
    levels_results = []
    passed_levels = []
    failed_at = None
    all_passed = False

    for level_num in range(start_level, 6):
        result = grade_prompt(
            user_prompt=user_prompt.strip(),
            level_number=level_num,
            domain=domain,
            api_key=resolved_key,
            model=model,
        )
        result["error"] = False
        result["raw_json"] = json.dumps(result, indent=2, ensure_ascii=False)
        result["from_fallback"] = not bool(resolved_key)

        level_entry = {
            "level": level_num,
            "result": result,
            "passed": result.get("verdict") == "pass",
            "xp": LEVEL_XP.get(level_num, 0) if result.get("verdict") == "pass" else 0,
        }
        levels_results.append(level_entry)

        if result.get("verdict") == "pass":
            passed_levels.append(level_num)
        else:
            failed_at = level_num
            break

    if len(passed_levels) == 5:
        all_passed = True

    total_xp = sum(LEVEL_XP.get(l, 0) for l in passed_levels)
    completion_pct = int((len(passed_levels) / 5) * 100)

    return {
        "error": False,
        "levels": levels_results,
        "passed_levels": passed_levels,
        "failed_at": failed_at,
        "all_passed": all_passed,
        "total_passed": len(passed_levels),
        "total_xp": total_xp,
        "completion_pct": completion_pct,
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_strength(result: dict) -> int:
    criteria = result.get("criteria", {})
    if not criteria:
        return 0
    passed = sum(1 for c in criteria.values() if c.get("pass", False))
    total = len(criteria)
    base = int((passed / total) * 70)
    grade_bonus = {"S": 30, "A": 20, "B": 10, "C": 5, "D": 0}
    grade = result.get("grade", "D")
    return min(base + grade_bonus.get(grade, 0), 100)


def _render_confetti(count: int = 40):
    colors = ["#60A5FA", "#22C55E", "#F59E0B", "#EF4444", "#A78BFA", "#F9A8D4", "#6EE7B7", "#FBBF24"]
    pieces = ""
    for i in range(count):
        left = 2 + (i * 2.5) % 96
        delay = (i * 0.06) % 2.0
        color = colors[i % len(colors)]
        w = 4 + (i % 4) * 2
        h = 4 + (i % 3) * 2
        pieces += f'<div class="confetti-piece" style="left:{left}%;background:{color};animation-delay:{delay}s;width:{w}px;height:{h}px;"></div>'
    return pieces


def _render_celebration_modal(level_num: int, xp: int, passed: list, total: int):
    msg = CELEBRATION_MESSAGES.get(level_num, {})
    confetti = _render_confetti()
    pct = int((len(passed) / 5) * 100)
    level_dots = ""
    for l in range(1, 6):
        if l in passed:
            level_dots += f'<span style="color:#22C55E;font-size:1.2rem;">●</span>'
        elif l == level_num and level_num not in passed:
            level_dots += f'<span style="color:#60A5FA;font-size:1.2rem;">◉</span>'
        else:
            level_dots += f'<span style="color:#334155;font-size:1.2rem;">○</span>'
        if l < 5:
            level_dots += f'<span style="color:#334155;font-size:0.8rem;margin:0 2px;">→</span>'
    modal = f"""
    {confetti}
    <div class="celebration-overlay" id="celeb-overlay">
        <div class="celebration-modal">
            <div class="celebration-icon">{level_num} of 5!</div>
            <div class="celebration-title">{msg.get("title", "Level Cleared!")}</div>
            <div class="celebration-subtitle">{msg.get("subtitle", "")}</div>
            <div style="margin:0.5rem 0;font-size:0.8rem;color:#64748B;">{level_dots}</div>
            <div class="celebration-xp">+{xp} XP</div>
            <div style="font-size:0.75rem;color:#94A3B8;margin:0.5rem 0;">{len(passed)}/5 Levels · {pct}% Complete</div>
            <div>
                <button onclick="document.getElementById('celeb-overlay').remove()" style="background:linear-gradient(135deg,#3B82F6,#2563EB);border:none;border-radius:10px;padding:0.5rem 2rem;color:white;font-weight:600;cursor:pointer;font-size:0.85rem;">
                    Continue →
                </button>
            </div>
        </div>
    </div>
    """
    return modal


def _render_victory_screen(data: dict):
    confetti = _render_confetti(60)
    passed = data.get("passed_levels", [])
    xp = data.get("total_xp", 0)
    grade = data.get("final_grade", "S")
    badges = ""
    for l in range(1, 6):
        icon = LEVEL_ICONS.get(l, "⭐")
        name = LEVEL_NAMES.get(l, "")
        badges += f'<div style="display:inline-flex;align-items:center;gap:0.4rem;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);border-radius:20px;padding:0.3rem 0.8rem;margin:0.2rem;"><span>{icon}</span><span style="font-size:0.75rem;color:#22C55E;">{name}</span></div> '
    modal = f"""
    {confetti}
    <div class="celebration-overlay" id="victory-overlay">
        <div class="celebration-modal grand" style="max-width:500px;">
            <div style="font-size:4rem;margin-bottom:0.5rem;">🏆</div>
            <div class="celebration-title" style="font-size:1.6rem;">PROMPT MASTER ACHIEVED</div>
            <div class="celebration-subtitle">Your prompt passed all 5 challenges.</div>
            <div style="margin:1rem 0;">
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;">
                    <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:8px;padding:0.5rem;">
                        <div style="font-size:1.2rem;font-weight:700;color:#F1F5F9;">{len(passed)}</div>
                        <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;">Levels</div>
                    </div>
                    <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:8px;padding:0.5rem;">
                        <div style="font-size:1.2rem;font-weight:700;color:#F59E0B;">{xp}</div>
                        <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;">XP</div>
                    </div>
                    <div style="background:rgba(30,41,59,0.7);border:1px solid #334155;border-radius:8px;padding:0.5rem;">
                        <div style="font-size:1.2rem;font-weight:700;color:#22C55E;">{grade}</div>
                        <div style="font-size:0.6rem;color:#64748B;text-transform:uppercase;">Grade</div>
                    </div>
                </div>
            </div>
            <div style="margin-bottom:0.8rem;">{badges}</div>
            <div>
                <button onclick="document.getElementById('victory-overlay').remove()" style="background:linear-gradient(135deg,#F59E0B,#D97706);border:none;border-radius:10px;padding:0.6rem 2rem;color:white;font-weight:700;cursor:pointer;font-size:0.9rem;">
                    🎉 Claim Victory
                </button>
            </div>
        </div>
    </div>
    """
    return modal


def render_celebration():
    if st.session_state.get("show_celebration") and st.session_state.get("celebration_data"):
        data = st.session_state.celebration_data
        modal = _render_celebration_modal(data["level"], data["xp"], data.get("passed", []), data.get("total", 5))
        st.markdown(modal, unsafe_allow_html=True)
        st.session_state.show_celebration = False
        st.session_state.celebration_data = None

    if st.session_state.get("show_victory") and st.session_state.get("victory_data"):
        modal = _render_victory_screen(st.session_state.victory_data)
        st.markdown(modal, unsafe_allow_html=True)
        st.session_state.show_victory = False
        st.session_state.victory_data = None


def render_level_badges(result: dict):
    criteria = result.get("criteria", {})
    for crit_name, crit_data in criteria.items():
        passed = crit_data.get("pass", False)
        display_name = crit_name.replace("_", " ").title()
        if passed:
            st.markdown(f'<div class="criterion-item criterion-pass"><div class="criterion-name">✅ {display_name}</div><div class="criterion-status-pass">✓ Passed</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="criterion-item criterion-fail"><div class="criterion-name">❌ {display_name}</div><div class="criterion-status-fail">✗ Needs Improvement</div></div>', unsafe_allow_html=True)


def render_line_analysis(result: dict):
    lines = result.get("line_analysis", [])
    if not lines:
        return
    st.markdown("### 🔬 Line-by-Line Analysis")
    for item in lines:
        phrase = item.get("line_or_phrase", "")
        issue = item.get("issue", "")
        why = item.get("why_it_matters", "")
        severity = item.get("severity", "medium")
        question = item.get("guiding_question", "")
        sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "🟡")
        html = f'<div class="line-analysis-item">'
        if phrase:
            html += f'<div class="line-phrase">"{phrase}"</div>'
        if issue:
            html += f'<div class="line-issue">{sev_icon} {issue} <span style="font-size:0.65rem;text-transform:uppercase;">[{severity}]</span></div>'
        if why:
            html += f'<div class="line-why">💡 {why}</div>'
        if question:
            html += f'<div class="line-question">❓ {question}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


def render_top_bar(passed: list = None, xp: int = 0, strength: int = 0):
    if passed is None:
        passed = []
    pct = int((len(passed) / 5) * 100)
    c1, c2, c3 = st.columns([0.18, 0.47, 0.35])
    with c1:
        st.markdown('<div style="display:flex;align-items:center;gap:0.4rem;"><span style="font-size:1.4rem;">🔥</span><div><div class="app-title">Prompt Doctor</div><div class="app-subtitle">Prompt Engineering Challenge</div></div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="progress-container"><div class="progress-bar-track"><div class="progress-bar-fill" style="width:{pct}%;"></div></div><span class="progress-text">{pct}%</span></div>', unsafe_allow_html=True)
        label = f"{len(passed)}/5 Levels · {xp} XP"
        if strength > 0:
            label += f" · Strength: {strength}%"
        st.markdown(f'<div style="font-size:0.7rem;color:#64748B;text-align:right;">{label}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-grid"><div class="stat-card"><div class="stat-value">{len(passed)}</div><div class="stat-label">Levels</div></div><div class="stat-card"><div class="stat-value">{xp}</div><div class="stat-label">XP</div></div><div class="stat-card"><div class="stat-value">{pct}%</div><div class="stat-label">Done</div></div></div>', unsafe_allow_html=True)
    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)


def render_current_level_card(level_num: int):
    if level_num > 5:
        return
    level_info = get_level(level_num)
    st.markdown(f"""
    <div class="glass-card" style="padding:0.8rem 1rem;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
            <div>
                <span style="font-size:1.3rem;">{level_info['icon']}</span>
                <span style="font-weight:700;font-size:0.9rem;color:#F1F5F9;margin-left:0.5rem;">Level {level_num}: {level_info['name']}</span>
                <span style="font-size:0.65rem;color:#64748B;margin-left:0.5rem;">{level_info['difficulty_label']}</span>
            </div>
        </div>
        <div style="margin-top:0.4rem;font-size:0.72rem;color:#94A3B8;">{level_info['description'][:120]}...</div>
        <div style="margin-top:0.4rem;">
            <span style="font-size:0.65rem;color:#64748B;">🎯 {level_info['pass_condition']}</span>
        </div>
        <div class="strength-meter"><div class="strength-fill" style="width:0%;background:#334155;"></div></div>
    </div>
    """, unsafe_allow_html=True)


def render_level_roadmap(passed: list, failed_at=None):
    st.markdown('<div class="section-title">🗺️ Level Progress</div>')
    for l in range(1, 6):
        level_data = get_level(l)
        if l in passed:
            cls, badge, text, icon = "passed", "passed-badge", "✓ PASSED", "✅"
        elif failed_at and l == failed_at:
            cls, badge, text, icon = "failed", "failed-badge", "✗ FAILED", "❌"
        elif l == 1 or (l - 1) in passed:
            if not failed_at:
                cls, badge, text, icon = "active", "active-badge", "ACTIVE", "▶"
            else:
                cls, badge, text, icon = "locked", "locked-badge", "LOCKED", "🔒"
        else:
            cls, badge, text, icon = "locked", "locked-badge", "LOCKED", "🔒"
        st.markdown(
            f'<div class="level-card {cls}">'
            f'<span class="level-icon">{level_data["icon"]}</span>'
            f'<span class="level-name">Level {l}: {level_data["name"]}</span>'
            f'<span class="level-badge {badge}">{text}</span>'
            f'<span style="float:right;font-size:1rem;color:#64748B;">{icon}</span>'
            f'<div style="font-size:0.65rem;color:#64748B;margin-top:0.1rem;">{level_data["difficulty_label"]}</div>'
            f'</div>', unsafe_allow_html=True)


def render_auto_results(auto_result: dict):
    levels_data = auto_result.get("levels", [])
    passed = auto_result.get("passed_levels", [])
    failed_at = auto_result.get("failed_at")
    all_passed = auto_result.get("all_passed", False)
    total_xp = auto_result.get("total_xp", 0)
    total_passed = auto_result.get("total_passed", 0)
    strength = auto_result.get("strength", 0)

    for entry in levels_data:
        lvl = entry["level"]
        result = entry["result"]
        passed_bool = entry["passed"]
        xp = entry["xp"]
        status_color = "#22C55E" if passed_bool else "#EF4444"
        status_icon = "✅" if passed_bool else "❌"
        status_text = "PASSED" if passed_bool else "FAILED"

        st.markdown(
            f'<div class="glass-card fade-in" style="padding:0.7rem 1rem;border-left:4px solid {status_color};">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div><span style="font-size:1.2rem;">{LEVEL_ICONS.get(lvl, "⭐")}</span> '
            f'<span style="font-weight:600;font-size:0.85rem;color:#F1F5F9;">Level {lvl}: {LEVEL_NAMES.get(lvl, "")}</span></div>'
            f'<div style="display:flex;align-items:center;gap:0.8rem;">'
            f'<span style="font-size:0.8rem;font-weight:600;color:{status_color};">{status_icon} {status_text}</span>'
            f'<span style="font-size:0.7rem;color:#64748B;">Grade: {result.get("grade","D")}</span>'
            + (f'<span class="xp-display" style="font-size:0.65rem;">+{xp} XP</span>' if passed_bool else "") +
            f'</div></div>',
            unsafe_allow_html=True)

        with st.expander(f"📋 Details for Level {lvl}", expanded=(not passed_bool and lvl == failed_at)):
            st.markdown(f'<div class="understanding-box"><strong>📖 Understanding:</strong> {result.get("understanding", "")}</div>', unsafe_allow_html=True)
            feedback = result.get("overall_feedback", "")
            if feedback:
                st.markdown(f'<div class="feedback-box"><strong>💬 Feedback:</strong><br>{feedback}</div>', unsafe_allow_html=True)
            if result.get("from_fallback"):
                st.markdown('<div class="info-banner">⚠️ Local fallback analysis (no API key).</div>', unsafe_allow_html=True)
            render_level_badges(result)
            render_line_analysis(result)
            with st.expander("📄 Raw JSON", expanded=False):
                raw = result.get("raw_json", "")
                if raw:
                    try:
                        parsed = json.loads(raw) if isinstance(raw, str) else raw
                        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                    except (json.JSONDecodeError, TypeError):
                        formatted = str(raw)
                    st.markdown(f'<div class="json-box">{formatted}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)

    if all_passed:
        st.balloons()
        st.markdown(
            f'<div class="glass-card" style="text-align:center;padding:1.5rem;border:2px solid #F59E0B;background:rgba(245,158,11,0.05);">'
            f'<div style="font-size:3rem;">🏆</div>'
            f'<div style="font-size:1.4rem;font-weight:800;color:#F1F5F9;margin:0.3rem 0;">PROMPT MASTER ACHIEVED</div>'
            f'<div style="font-size:0.85rem;color:#94A3B8;">Your prompt passed all 5 levels!</div>'
            f'<div style="margin-top:0.8rem;">'
            f'<span style="font-size:0.9rem;color:#F59E0B;font-weight:700;">{total_xp} XP</span>'
            f'<span style="margin:0 1rem;color:#334155;">|</span>'
            f'<span style="font-size:0.9rem;color:#22C55E;font-weight:700;">{strength}% Strength</span>'
            f'</div></div>', unsafe_allow_html=True)
    elif failed_at:
        st.markdown(
            f'<div class="glass-card" style="text-align:center;padding:1rem;border:2px solid #EF4444;background:rgba(239,68,68,0.05);">'
            f'<div style="font-size:1.2rem;font-weight:700;color:#F1F5F9;">⛔ Failed at Level {failed_at}</div>'
            f'<div style="font-size:0.8rem;color:#94A3B8;margin-top:0.3rem;">{total_passed}/5 levels cleared · {total_xp} XP earned</div>'
            f'<div style="margin-top:0.5rem;font-size:0.75rem;color:#FDE68A;">'
            f'💡 Improve your prompt based on the Examiner feedback and try again!'
            f'</div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# MAIN APP
# ---------------------------------------------------------------------------

render_celebration()

auto_result = st.session_state.get("auto_result")
if auto_result:
    passed = auto_result.get("passed_levels", [])
    total_xp = auto_result.get("total_xp", 0)
    strength = auto_result.get("strength", 0)
else:
    passed = []
    total_xp = 0
    strength = 0

render_top_bar(passed=passed, xp=total_xp, strength=strength)

cols = st.columns([0.38, 0.62], gap="large")
left_col, right_col = cols[0], cols[1]

with left_col:
    next_level = (max(passed) + 1) if passed else 1
    if next_level <= 5:
        render_current_level_card(next_level)
    else:
        st.markdown('<div class="glass-card" style="text-align:center;padding:1.2rem;border:2px solid #F59E0B;"><div style="font-size:2.5rem;">🏆</div><div style="font-size:1.1rem;font-weight:700;color:#F1F5F9;">Challenge Complete!</div><div style="font-size:0.8rem;color:#94A3B8;">You mastered all 5 levels.</div></div>', unsafe_allow_html=True)

    if next_level <= 5 and not auto_result:
        level_info = get_level(next_level)
        st.markdown(f'<div class="pass-condition-box">🎯 <strong>Pass Condition:</strong> {level_info["pass_condition"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="reward-box">🎁 <strong>Reward:</strong> {level_info["reward"]}</div>', unsafe_allow_html=True)

    st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Settings")
    domains = get_domains()
    selected_domain = st.selectbox("Domain", options=domains, index=0)

    st.markdown("### ✍️ Your Prompt")
    user_prompt = st.text_area("Enter your prompt:", height=160,
        placeholder='Write your prompt here...\n\nExample: "Act as a legal expert. Analyze this contract clause..."',
        label_visibility="collapsed")
    if user_prompt:
        wc = len(user_prompt.strip().split())
        st.caption(f"📊 {wc} words")

    st.markdown("<br>", unsafe_allow_html=True)
    evaluate_disabled = st.session_state.evaluating or not user_prompt.strip()
    if not user_prompt.strip():
        st.caption("Enter a prompt to begin.")
    else:
        col_btn, col_info = st.columns([0.6, 0.4])
        with col_btn:
            evaluate_button = st.button("🚀 Evaluate Through All Levels", type="primary", use_container_width=True, disabled=evaluate_disabled)
        with col_info:
            st.markdown(f'<div style="font-size:0.7rem;color:#94A3B8;text-align:right;padding-top:0.5rem;"><span class="xp-display">Up to 1,900 XP</span></div>', unsafe_allow_html=True)

    with st.expander("🔑 API Config", expanded=False):
        api_key = st.text_input("OpenRouter API Key", type="password", placeholder="sk-or-v1-...")
        model = st.text_input("Model", value="deepseek/deepseek-r1:free")

    st.markdown("---")
    render_level_roadmap(passed, auto_result.get("failed_at") if auto_result else None)

with right_col:
    st.markdown('<div class="right-panel">', unsafe_allow_html=True)
    st.markdown("### 📋 Examiner Results")
    results_placeholder = st.empty()

    if evaluate_button and user_prompt.strip():
        st.session_state.evaluating = True
        st.session_state.error_message = None
        st.session_state.submission_count += 1
        with results_placeholder.container():
            with st.spinner("🔍 The Examiner is evaluating your prompt through all levels..."):
                time.sleep(0.2)
                try:
                    resolved_key = api_key or os.getenv("OPENROUTER_API_KEY")
                    auto_result = evaluate_auto(
                        user_prompt=user_prompt,
                        start_level=1,
                        domain=selected_domain,
                        api_key=resolved_key if resolved_key else None,
                        model=model if api_key else "deepseek/deepseek-r1:free",
                    )
                    strengths = []
                    for e in auto_result.get("levels", []):
                        s = _compute_strength(e["result"])
                        strengths.append(s)
                    avg_strength = int(sum(strengths) / len(strengths)) if strengths else 0
                    auto_result["strength"] = avg_strength
                    st.session_state.auto_result = auto_result

                    passed_levels = auto_result.get("passed_levels", [])
                    if auto_result.get("all_passed"):
                        final_grade = auto_result["levels"][-1]["result"]["grade"] if auto_result["levels"] else "S"
                        st.session_state.victory_data = {"passed_levels": passed_levels, "total_xp": auto_result.get("total_xp", 0), "final_grade": final_grade, "strength": avg_strength}
                        st.session_state.show_victory = True
                    elif passed_levels:
                        highest = max(passed_levels)
                        xp = LEVEL_XP.get(highest, 0)
                        st.session_state.celebration_data = {"level": highest, "xp": xp, "passed": passed_levels, "total": 5}
                        st.session_state.show_celebration = True
                except Exception as e:
                    st.session_state.error_message = f"Evaluation failed: {str(e)}"
                    st.session_state.auto_result = None
                finally:
                    st.session_state.evaluating = False
        if st.session_state.get("show_celebration") or st.session_state.get("show_victory"):
            st.rerun()

    auto_result = st.session_state.get("auto_result")
    error_message = st.session_state.get("error_message")
    if error_message:
        with results_placeholder.container():
            st.error(f"⚠️ {error_message}")
    elif auto_result:
        with results_placeholder.container():
            render_auto_results(auto_result)
    else:
        with results_placeholder.container():
            st.markdown(
                '<div class="empty-state fade-in">'
                '<div class="empty-state-icon">🔍</div>'
                '<div class="empty-state-title">Awaiting Evaluation</div>'
                '<div class="empty-state-desc">'
                "Enter a prompt and click <strong>Evaluate Through All Levels</strong>.<br>"
                "The Examiner will test your prompt against all 5 levels automatically."
                '</div></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<hr class="custom-divider">', unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:#64748B;font-size:0.7rem;padding-bottom:1.5rem;'>🔥 Prompt Doctor 2.0 — Prompt Engineering Challenge · Powered by OpenRouter & Streamlit</div>", unsafe_allow_html=True)