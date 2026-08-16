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
@st.cache_data
def load_data():
    df = pd.read_csv("data.csv")
    df["Topic Tags"] = df["Topic Tags"].apply(lambda s: [t.strip() for t in s.split(";")])
    df["Audience Tags"] = df["Audience Tags"].apply(lambda s: [t.strip() for t in s.split(";")])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    return df

df = load_data()

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


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "persona" not in st.session_state:
    st.session_state.persona = "clinical_lead"
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="gpn-header">
        <p class="gpn-eyebrow">Global Policy Network · Prototype</p>
        <p class="gpn-title">AI Healthcare Intelligence Dashboard</p>
        <p class="gpn-sub">Public healthcare updates, organised and explained — with a persona
        lens so the same update reads differently for a clinician, a policy manager, or a
        trust operations lead.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Persona selector
# ---------------------------------------------------------------------------
st.markdown("**Reading as**")
cols = st.columns(3)
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

st.divider()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")
    search = st.text_input("Search updates", "")
    topic_filter = st.multiselect("Topic", ALL_TOPICS)
    audience_filter = st.multiselect("Relevant to", ALL_AUDIENCES)
    if st.button("Clear all filters"):
        search, topic_filter, audience_filter = "", [], []
        st.rerun()

# ---------------------------------------------------------------------------
# Filter + score
# ---------------------------------------------------------------------------
filtered = df.copy()
if topic_filter:
    filtered = filtered[filtered["Topic Tags"].apply(lambda tags: any(t in tags for t in topic_filter))]
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
    with st.container(border=True):
        head_col, score_col = st.columns([5, 1])
        with head_col:
            st.markdown(f"**{row['Title']}**")
            st.caption(f"{row['Source']} · {row['Date']} · {row['Source Type']}")
            tag_html = "".join(f'<span class="badge badge-topic">{t}</span>' for t in row["Topic Tags"])
            tag_html += "".join(f'<span class="badge badge-audience">{a}</span>' for a in row["Audience Tags"])
            st.markdown(tag_html, unsafe_allow_html=True)
        with score_col:
            st.metric("Match", f"{row['Relevance']}%")

        with st.expander("View AI-generated insight"):
            c1, c2 = st.columns(2)
            fields = [
                ("What changed", row["What Changed"]),
                ("Why it matters", row["Why It Matters"]),
                ("Who it affects", row["Who It Affects"]),
                ("Suggested action", row["Suggested Action"]),
            ]
            for i, (label, text) in enumerate(fields):
                target = c1 if i % 2 == 0 else c2
                is_focus = label.lower().replace("suggested ", "") in [f.lower().replace("suggested ", "") for f in active["focus"]]
                with target:
                    if is_focus:
                        st.markdown(
                            f"<div style='background:{PALETTE['teal_soft']}; padding:8px 10px; "
                            f"border-radius:6px; margin-bottom:8px;'>"
                            f"<span style='font-size:10.5px; text-transform:uppercase; "
                            f"letter-spacing:.05em; color:{PALETTE['teal']};'>{label}</span><br>"
                            f"{text}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(f"**{label}**")
                        st.write(text)
            st.markdown(f"[View original source ↗]({row['URL']})")
            st.caption(f"Source reliability: {reliability_badge(row['Reliability'])} — {row['Reliability']}")

st.divider()
st.caption(
    "Prototype for a Global Policy Network placement project. Sample of 25 public healthcare "
    "updates (Jan–Aug 2026) from NHS England, NICE, DHSC/GOV.UK, UKHSA, The King's Fund, The "
    "Health Foundation, NHS Confederation and trade press. AI insights are template-generated "
    "for demonstration; every card links to its original public source."
)