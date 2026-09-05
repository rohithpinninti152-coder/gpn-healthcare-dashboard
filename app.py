"""
Global Policy Network — AI Healthcare Intelligence Dashboard
Streamlit prototype: browsable healthcare updates with persona-based re-ranking.

Run with:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="GPN — AI Healthcare Intelligence Dashboard",
    page_icon="🩺",
    layout="wide",
)

PALETTE = {
    "navy": "#1B2430",
    "teal": "#2F6F5E",
    "teal_soft": "#E6EFEC",
    "violet": "#5A4A9E",
    "violet_soft": "#EEECF7",
    "amber": "#A3641F",
    "amber_soft": "#F5EAD9",
    "paper": "#F6F4EF",
    "line": "#E2DDD0",
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
PRIMARY_SOURCE_MAP = {
    "Digital Health News": "Digital Health News",
    "Digital Health News / NHS Shared Business Services": "Digital Health News",
    "EMJ Reviews, citing NHS England / King's Fund analysis": "EMJ Reviews",
    "GOV.UK / DHSC": "GOV.UK / DHSC",
    "GOV.UK / DHSC, DSIT, NHS England": "GOV.UK / DHSC",
    "GOV.UK — UKHSA": "UKHSA",
    "NHS Confederation": "NHS Confederation",
    "NHS Confederation, citing HSJ": "NHS Confederation",
    "NHS England": "NHS England",
    "NHS England (London)": "NHS England",
    "Prescriber.org.uk (NICE guidance digest)": "NICE",
    "The Health Foundation": "The Health Foundation",
    "The King's Fund": "The King's Fund",
    "The Pharmaceutical Journal": "The Pharmaceutical Journal",
    "UK Parliament — Written Ministerial Statement": "UK Parliament",
    "UKHSA (via Streamlinefeed / gov.uk reporting)": "UKHSA",
    "UKHSA / Met Office (via ITV News, GOV.UK)": "UKHSA",
}


def map_primary_source(source: str) -> str:
    return PRIMARY_SOURCE_MAP.get(source, source)


@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df["Topic Tags"] = df["Topic Tags"].apply(lambda s: [t.strip() for t in s.split(";")])
    df["Audience Tags"] = df["Audience Tags"].apply(lambda s: [t.strip() for t in s.split(";")])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Primary Source"] = df["Source"].apply(map_primary_source)
    return df

df = load_data()
ALL_SOURCES = sorted(df["Primary Source"].unique())

ALL_TOPICS = ["Policy", "Clinical Guidance", "Regulation", "Funding", "Technology", "Public Health", "Market"]
ALL_AUDIENCES = ["Clinicians", "Healthcare Managers", "Policy Teams", "Commissioners", "Industry Stakeholders", "Patients"]

PERSONAS = {
    "clinical_lead": {
        "name": "Dr. Amara Osei",
        "role": "Clinical Lead / Consultant Physician",
        "color": PALETTE["teal"],
        "match_topics": ["Clinical Guidance", "Public Health"],
        "match_audience": ["Clinicians", "Patients"],
        "focus": ["What Changed", "Suggested Action"],
        "preferred": "A short clinical summary: what changed, the evidence behind it, "
                      "and what to do differently in practice.",
    },
    "policy_manager": {
        "name": "Daniel Ferris",
        "role": "Policy & Commissioning Manager, ICB",
        "color": PALETTE["violet"],
        "match_topics": ["Policy", "Funding", "Regulation"],
        "match_audience": ["Policy Teams", "Commissioners"],
        "focus": ["Why It Matters", "Who It Affects"],
        "preferred": "A policy and system-impact summary: what changed, why it matters "
                      "for commissioning, and what funding implications follow.",
    },
    "trust_manager": {
        "name": "Priya Chandra",
        "role": "NHS Trust Digital & Operations Manager",
        "color": PALETTE["amber"],
        "match_topics": ["Technology", "Market"],
        "match_audience": ["Healthcare Managers", "Industry Stakeholders"],
        "focus": ["Suggested Action", "What Changed"],
        "preferred": "An operational and market summary: what's changing, what it "
                      "costs or requires to adopt, and what to do about it.",
    },
    "policy_maker_amina": {
        "name": "Amina Yusuf",
        "role": "Senior Policy Maker, Department of Health and Social Care",
        "color": "#8a4b6b",
        "match_topics": ["Policy", "Regulation", "Public Health"],
        "match_audience": ["Policy Teams", "Industry Stakeholders"],
        "focus": ["Who It Affects", "Why It Matters"],
        "preferred": "A national-policy framing: how an update fits wider legislation "
                      "or strategy, who it affects at population scale, and what "
                      "coordination across departments or regulators it implies.",
    },
}

# ---------------------------------------------------------------------------
# Relevance scoring — mirrors the HTML prototype's JS logic
# ---------------------------------------------------------------------------
def relevance(row, persona):
    score = sum(2 for t in row["Topic Tags"] if t in persona["match_topics"])
    score += sum(1.5 for a in row["Audience Tags"] if a in persona["match_audience"])
    max_score = 2 * len(persona["match_topics"]) + 1.5 * len(persona["match_audience"])
    return max(8, round((score / max_score) * 100)) if max_score else 8


def display_first_name(full_name: str) -> str:
    """Return a friendly first name for headings, skipping honorifics like 'Dr.'."""
    parts = full_name.split()
    for part in parts:
        if part.rstrip(".").isalpha() and part.rstrip(".").lower() not in {"dr", "mr", "mrs", "ms", "prof"}:
            return part
    return parts[0] if parts else full_name


def reliability_badge(text: str) -> str:
    if text.startswith("High"):
        return "🟢 High"
    if text.startswith("Medium-High"):
        return "🟡 Medium-high"
    if text.startswith("Medium"):
        return "🟠 Medium"
    return "⚪ Low"


def reliability_score_10(text: str) -> float:
    """Numeric reliability score out of 10, for the 'signal strength' bar."""
    if text.startswith("High"):
        return 9.5
    if text.startswith("Medium-High"):
        return 7.0
    if text.startswith("Medium"):
        return 5.5
    return 4.0


def urgency_level(relevance_pct: int) -> tuple:
    """Derive an urgency label + color from the persona relevance score."""
    if relevance_pct >= 70:
        return "High urgency", PALETTE["amber"], "#F5DCC8"
    if relevance_pct >= 40:
        return "Medium urgency", PALETTE["violet"], PALETTE["violet_soft"]
    return "Low urgency", "#6b7280", "#e9e9e9"


def bar_heights(seed_text: str) -> list:
    """Deterministic-but-varied bar heights for the decorative mini chart, seeded by title."""
    h = abs(hash(seed_text))
    return [30 + (h >> (i * 4) & 0xF) * 4 for i in range(5)]


def time_ago(update_date, reference_date) -> str:
    """A relative 'time ago' label, e.g. '3 days ago' — calculated against the
    dataset's own most recent update, not real wall-clock time, since this is
    a fixed historical sample rather than a live feed."""
    days = (reference_date - update_date).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "1 day ago"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "1 week ago"
    if days < 30:
        return f"{days // 7} weeks ago"
    if days < 60:
        return "1 month ago"
    if days < 365:
        return f"{days // 30} months ago"
    years = days // 365
    return "1 year ago" if years == 1 else f"{years} years ago"


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "persona" not in st.session_state:
    st.session_state.persona = "clinical_lead"
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "page" not in st.session_state:
    st.session_state.page = "landing"

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {PALETTE['paper']}; }}
    .gpn-header {{
        background: {PALETTE['navy']}; color: #f1efe8; padding: 20px 26px;
        border-radius: 10px; margin-bottom: 18px; border-bottom: 4px solid {PALETTE['teal']};
    }}
    .gpn-eyebrow {{ font-size: 11px; letter-spacing: .14em; text-transform: uppercase;
        color: #9fb3ac; margin: 0 0 4px; font-family: monospace; }}
    .gpn-title {{ font-size: 26px; font-weight: 700; margin: 0 0 4px; }}
    .gpn-sub {{ font-size: 13px; color: #c7cad3; margin: 0; }}
    .badge {{ display:inline-block; padding: 2px 9px; border-radius: 999px;
        font-size: 11px; margin-right: 5px; margin-bottom: 4px; }}
    .badge-topic {{ background: {PALETTE['teal_soft']}; color: {PALETTE['teal']}; }}
    .badge-audience {{ background: {PALETTE['violet_soft']}; color: {PALETTE['violet']}; }}
    .gpn-stat-card {{
        background: {PALETTE['navy']}; border-radius: 10px; padding: 18px 20px;
        text-align: center; color: #f1efe8;
    }}
    .gpn-stat-number {{ font-size: 32px; font-weight: 700; color: {PALETTE['teal']}; margin: 0; }}
    .gpn-stat-label {{ font-size: 12px; color: #c7cad3; margin: 4px 0 0; text-transform: uppercase;
        letter-spacing: .06em; }}

    /* Intelligence brief card */
    .brief-card {{
        display: grid; grid-template-columns: 140px 1fr; gap: 0;
        background: {PALETTE['paper_card'] if 'paper_card' in PALETTE else '#ffffff'};
        border: 0.5px solid {PALETTE['line']}; border-radius: 14px; overflow: hidden;
        margin-bottom: 18px;
    }}
    .brief-sidepanel {{
        background: linear-gradient(160deg, {PALETTE['navy']} 0%, {PALETTE['teal']} 130%);
        padding: 18px 14px; display: flex; flex-direction: column; justify-content: space-between;
        color: #fff; min-height: 100%;
    }}
    .brief-sysmap {{
        display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,.14);
        border-radius: 999px; padding: 4px 10px; font-size: 10.5px; font-weight: 600;
        letter-spacing: .04em; width: fit-content;
    }}
    .brief-bars {{ display: flex; align-items: flex-end; gap: 6px; height: 80px; margin: 18px 0; }}
    .brief-bar {{ width: 12px; background: rgba(255,255,255,.55); border-radius: 3px; }}
    .brief-signal-label {{ font-size: 10px; letter-spacing: .06em; text-transform: uppercase;
        opacity: .85; display: flex; justify-content: space-between; margin-bottom: 4px; }}
    .brief-signal-bar {{ height: 5px; background: rgba(255,255,255,.25); border-radius: 4px; overflow: hidden; }}
    .brief-signal-fill {{ height: 100%; background: #fff; border-radius: 4px; }}
    .brief-main {{ padding: 18px 22px; }}
    .brief-top-row {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
    .brief-tags {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .brief-tag {{ font-size: 11.5px; font-weight: 600; padding: 4px 11px; border-radius: 999px; }}
    .brief-relevance-box {{
        text-align: right; background: {PALETTE['paper']}; border: 0.5px solid {PALETTE['line']};
        border-radius: 8px; padding: 6px 12px; flex: none;
    }}
    .brief-relevance-label {{ font-size: 9.5px; color: {PALETTE['muted'] if 'muted' in PALETTE else '#6b7280'};
        letter-spacing: .06em; }}
    .brief-relevance-value {{ font-size: 18px; font-weight: 700; color: {PALETTE['navy']}; }}
    .brief-title {{ font-size: 19px; font-weight: 700; color: {PALETTE['navy']}; margin: 12px 0 4px; line-height: 1.3; }}
    .brief-meta {{ font-size: 12.5px; color: #6b7280; margin-bottom: 10px; display:flex; align-items:center; gap:8px; }}
    .brief-time-ago {{ font-size: 10.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px;
        background: #eef2f7; color: #4b5563; }}
    .brief-desc {{ font-size: 13.5px; color: #374151; line-height: 1.55; margin-bottom: 14px; }}
    .brief-info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .brief-info-box {{ border-radius: 8px; padding: 12px 14px; }}
    .brief-info-label {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase;
        letter-spacing: .05em; margin-bottom: 4px; }}
    .brief-info-text {{ font-size: 13px; line-height: 1.5; color: #1f2937; }}

    /* Landing page */
    .landing-hero {{
        background: linear-gradient(160deg, {PALETTE['navy']} 0%, {PALETTE['teal']} 130%);
        border-radius: 16px; padding: 44px 40px; color: #f1efe8; margin-bottom: 24px;
    }}
    .landing-section-title {{ font-size: 22px; font-weight: 700; color: {PALETTE['navy']};
        margin: 34px 0 6px; }}
    .use-card, .benefit-card {{
        background: #ffffff; border: 0.5px solid {PALETTE['line']}; border-radius: 10px;
        padding: 16px 18px; height: 100%;
    }}
    .use-card h4, .benefit-card h4 {{ margin: 0 0 6px; font-size: 14.5px; color: {PALETTE['navy']}; }}
    .use-card p, .benefit-card p {{ margin: 0; font-size: 13px; color: #4b5563; line-height: 1.5; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# NOTE: the landing/intro page (hero + "who this is for" + benefits) was
# removed for now, on request, so the dashboard opens directly and the core
# features (logo, last-updated, filters, personas, questionnaire) are
# immediately visible without an extra click. The landing page content is
# kept in landing_page_backup.py if it's wanted again later.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
last_updated = df["Date"].max().strftime("%d %b %Y")
st.markdown(
    f"""
    <div class="gpn-header">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="width:34px; height:34px; border-radius:8px; background:{PALETTE['teal']};
                    display:flex; align-items:center; justify-content:center; font-weight:700; font-size:14px;
                    color:#fff; flex:none;">GPN</div>
                <div>
                    <p class="gpn-eyebrow" style="margin:0;">Global Policy Network · Prototype</p>
                    <a href="https://www.GlobalPolicyNetwork.com" target="_blank"
                       style="font-size:11px; color:#9fb3ac;">www.GlobalPolicyNetwork.com</a>
                </div>
            </div>
            <div style="text-align:right; font-size:11px; color:#9fb3ac;">Last updated<br>
                <span style="color:#f1efe8; font-weight:600;">{last_updated}</span></div>
        </div>
        <p class="gpn-title" style="margin-top:14px;">AI Healthcare Intelligence Dashboard</p>
        <p class="gpn-sub">Public healthcare updates, organised and explained — with a persona
        lens so the same update reads differently for a clinician, a policy manager, or a
        trust operations lead.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Stat strip — shown on the main dashboard too, like the reference site
# ---------------------------------------------------------------------------
stat_cols = st.columns(3)
stats = [(str(len(df)), "Live intelligence briefs"), ("7", "Topic streams"), ("UK", "NHS market focus")]
for col, (num, label) in zip(stat_cols, stats):
    with col:
        st.markdown(
            f"""<div class="gpn-stat-card"><p class="gpn-stat-number">{num}</p>
            <p class="gpn-stat-label">{label}</p></div>""",
            unsafe_allow_html=True,
        )
st.write("")

# ---------------------------------------------------------------------------
# Top filter bar — category / source buttons (added per tutor feedback:
# filters should also be available as buttons/icons at the top of the page,
# not just tucked away in the sidebar)
# ---------------------------------------------------------------------------
st.markdown("**Filter by category**")
top_topic_filter = st.pills(
    "Topic", ALL_TOPICS, selection_mode="multi", label_visibility="collapsed", key="top_topic_pills"
)

st.markdown("**Filter by news source**")
top_source_filter = st.pills(
    "Source", ALL_SOURCES, selection_mode="multi", label_visibility="collapsed", key="top_source_pills"
)

st.markdown("**Filter by when published**")
DATE_RANGES = ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
date_range_choice = st.pills(
    "When", DATE_RANGES, selection_mode="single", default="All time",
    label_visibility="collapsed", key="date_range_pill"
)
st.caption(f"Relative to the most recent update in this sample ({last_updated}) — not today's real-world date.")

st.divider()

# ---------------------------------------------------------------------------
# Persona selector
# ---------------------------------------------------------------------------
st.markdown("**Reading as**")
cols = st.columns(4)
for col, (pid, p) in zip(cols, PERSONAS.items()):
    with col:
        label = f"{display_first_name(p['name'])} · {p['role'].split('/')[0].split(',')[0].strip()}"
        button_type = "primary" if st.session_state.persona == pid else "secondary"
        if st.button(label, key=f"persona_{pid}", use_container_width=True, type=button_type):
            st.session_state.persona = pid
            st.session_state.selected_id = None

active = PERSONAS[st.session_state.persona]

with st.expander(f"About this persona — {active['name']}, {active['role']}"):
    st.write(f"**Prefers:** {active['preferred']}")
    st.write(f"**Cares most about:** {', '.join(active['match_topics'])} topics, "
             f"for {', '.join(active['match_audience'])}.")

# ---------------------------------------------------------------------------
# Persona-matching questionnaire — helps a new user figure out which of the
# four personas fits them, without needing to know the personas up front.
# ---------------------------------------------------------------------------
QUESTIONNAIRE = [
    {
        "question": "Which best describes your day-to-day role?",
        "options": [
            ("Direct patient care / clinical practice", "clinical_lead"),
            ("Local commissioning or system planning (ICB)", "policy_manager"),
            ("Operations, digital or technology management", "trust_manager"),
            ("National policy, legislation or regulation", "policy_maker_amina"),
        ],
    },
    {
        "question": "What kind of update matters most to you?",
        "options": [
            ("New clinical guidance or treatment evidence", "clinical_lead"),
            ("Local funding or commissioning decisions", "policy_manager"),
            ("New technology, tools or market/supplier news", "trust_manager"),
            ("National legislation or regulatory change", "policy_maker_amina"),
        ],
    },
    {
        "question": "When you read an update, what do you want first?",
        "options": [
            ("What should I do differently in practice", "clinical_lead"),
            ("What it means for local budgets and decisions", "policy_manager"),
            ("What it means operationally, right now", "trust_manager"),
            ("Who it affects nationally and why it matters", "policy_maker_amina"),
        ],
    },
]

with st.expander("Not sure which persona fits you? Take the 1-minute questionnaire"):
    answers = {}
    for i, q in enumerate(QUESTIONNAIRE):
        choice = st.radio(q["question"], [opt[0] for opt in q["options"]], key=f"quiz_q{i}", index=None)
        if choice:
            answers[i] = dict(q["options"])[choice]

    if st.button("See my recommended persona"):
        if len(answers) < len(QUESTIONNAIRE):
            st.warning("Please answer all three questions first.")
        else:
            from collections import Counter
            st.session_state.quiz_winner = Counter(answers.values()).most_common(1)[0][0]

    # Kept outside the button's if-block (a common Streamlit gotcha: a button
    # nested inside another button's block never actually fires, because on
    # the rerun triggered by clicking it, the outer button's condition is
    # False again) so the result and switch action persist correctly.
    if st.session_state.get("quiz_winner"):
        winner = PERSONAS[st.session_state.quiz_winner]
        st.success(f"Based on your answers, your closest match is **{winner['name']}** — {winner['role']}.")
        if st.button(f"Switch to {display_first_name(winner['name'])}'s view"):
            st.session_state.persona = st.session_state.quiz_winner
            st.session_state.quiz_winner = None
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("More filters")
    search = st.text_input("Search updates", "")
    sidebar_topic_filter = st.multiselect("Topic", ALL_TOPICS)
    audience_filter = st.multiselect("Relevant to", ALL_AUDIENCES)
    if st.button("Clear all filters"):
        search, sidebar_topic_filter, audience_filter = "", [], []
        st.session_state.top_topic_pills = []
        st.session_state.top_source_pills = []
        st.rerun()

# Combine the top category pills with the sidebar's Topic multiselect —
# either one selecting a tag is enough to apply that filter.
topic_filter = list(set(top_topic_filter or []) | set(sidebar_topic_filter or []))

# ---------------------------------------------------------------------------
# Filter + score
# ---------------------------------------------------------------------------
filtered = df.copy()
if topic_filter:
    filtered = filtered[filtered["Topic Tags"].apply(lambda tags: any(t in tags for t in topic_filter))]
if top_source_filter:
    filtered = filtered[filtered["Primary Source"].isin(top_source_filter)]
if date_range_choice and date_range_choice != "All time":
    days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[date_range_choice]
    cutoff = df["Date"].max() - pd.Timedelta(days=days)
    filtered = filtered[filtered["Date"] >= cutoff]
if audience_filter:
    filtered = filtered[filtered["Audience Tags"].apply(lambda tags: any(a in tags for a in audience_filter))]
if search:
    s = search.lower()
    filtered = filtered[filtered.apply(
        lambda r: s in r["Title"].lower() or s in r["Source"].lower(), axis=1
    )]

filtered = filtered.copy()
filtered["Relevance"] = filtered.apply(lambda r: relevance(r, active), axis=1)
filtered = filtered.sort_values(["Relevance", "Date"], ascending=[False, False])

st.markdown(f"### Updates — {len(filtered)} of {len(df)} · sorted by relevance to {display_first_name(active['name'])}")

# ---------------------------------------------------------------------------
# Update list
# ---------------------------------------------------------------------------
if filtered.empty:
    st.info("No updates match these filters. Try clearing a filter in the sidebar.")

for _, row in filtered.iterrows():
    rel_pct = row["Relevance"]
    urgency_label, urgency_color, urgency_bg = urgency_level(rel_pct)
    signal = reliability_score_10(row["Reliability"])
    heights = bar_heights(row["Title"])
    primary_topic = row["Topic Tags"][0] if row["Topic Tags"] else "Update"
    ago_label = time_ago(row["Date"], df["Date"].max())

    bars_html = "".join(f'<div class="brief-bar" style="height:{h}px;"></div>' for h in heights)

    st.markdown(
        f"""
        <div class="brief-card">
          <div class="brief-sidepanel">
            <div>
              <span class="brief-sysmap">📊 SYSTEM MAP</span>
              <div class="brief-bars">{bars_html}</div>
            </div>
            <div>
              <div class="brief-signal-label"><span>SIGNAL STRENGTH</span><span>{signal:.1f}</span></div>
              <div class="brief-signal-bar"><div class="brief-signal-fill" style="width:{signal*10}%;"></div></div>
            </div>
          </div>
          <div class="brief-main">
            <div class="brief-top-row">
              <div class="brief-tags">
                <span class="brief-tag" style="background:{PALETTE['teal_soft']}; color:{PALETTE['teal']};">{primary_topic}</span>
                <span class="brief-tag" style="background:{urgency_bg}; color:{urgency_color};">{urgency_label}</span>
              </div>
              <div class="brief-relevance-box">
                <div class="brief-relevance-label">RELEVANCE</div>
                <div class="brief-relevance-value">{rel_pct/10:.1f} / 10</div>
              </div>
            </div>
            <div class="brief-title">{row['Title']}</div>
            <div class="brief-meta">{row['Source']} · {row['Date'].strftime('%d %b %Y')} <span class="brief-time-ago">{ago_label}</span></div>
            <div class="brief-desc">{row['What Changed']}</div>
            <div class="brief-info-grid">
              <div class="brief-info-box" style="background:{PALETTE['teal_soft']};">
                <div class="brief-info-label" style="color:{PALETTE['teal']};">Strategic Impact</div>
                <div class="brief-info-text">{row['Why It Matters']}</div>
              </div>
              <div class="brief-info-box" style="background:{PALETTE['violet_soft']};">
                <div class="brief-info-label" style="color:{PALETTE['violet']};">Recommended Action</div>
                <div class="brief-info-text">{row['Suggested Action']}</div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"View Intelligence Brief — {row['ID']}"):
        st.markdown(f"**Who it affects:** {row['Who It Affects']}")
        st.markdown(f"[View original source ↗]({row['URL']})")
        st.caption(f"Source reliability: {reliability_badge(row['Reliability'])} — {row['Reliability']}")
        aud_html = "".join(f'<span class="badge badge-audience">{a}</span>' for a in row["Audience Tags"])
        st.markdown(f"Relevant to: {aud_html}", unsafe_allow_html=True)

st.divider()
st.caption(
    "Prototype for a Global Policy Network placement project. Sample of 25 public healthcare "
    "updates (Jan–Aug 2026) from NHS England, NICE, DHSC/GOV.UK, UKHSA, The King's Fund, The "
    "Health Foundation, NHS Confederation and trade press. AI insights are template-generated "
    "for demonstration; every card links to its original public source."
)
