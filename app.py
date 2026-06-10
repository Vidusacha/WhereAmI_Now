import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import subprocess
from math import sqrt
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

DB_PATH = 'database/whereami_core.db'
st.set_page_config(page_title="WhereAmI Now", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")

# --- Load Locales ---
def load_locale(lang_code):
    path = os.path.join(os.path.dirname(__file__), 'locales', f'{lang_code}.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# --- Custom CSS ---
def inject_custom_css():
    direction = "rtl" if st.session_state.lang == "he" else "ltr"
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {{
        font-family: 'Inter', sans-serif;
        direction: {direction};
    }}
    
    /* Increase base fonts */
    p, span, .stMarkdown p, .stMarkdown span {{
        font-size: 1.15rem !important;
    }}
    
    .stApp {{
        background-color: #0f172a;
        color: #f8fafc;
    }}
    
    .glass-card {{
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 24px;
        height: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .glass-card:hover {{
        transform: translateY(-2px);
    }}
    
    h1 {{
        background: -webkit-linear-gradient(45deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }}
    
    .stButton>button {{
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }}
    .stButton>button:hover {{
        opacity: 0.9;
        transform: translateY(-2px);
    }}
    
    div[data-testid="stMetricValue"] {{
        font-size: 1.5rem !important;
    }}
    
    /* Sticky Header */
    div[data-testid="stVerticalBlock"] > div:has(#sticky-header) {{
        position: sticky;
        top: 0rem;
        z-index: 999;
        background-color: rgba(15, 23, 42, 0.95);
        backdrop-filter: blur(10px);
        padding-top: 2rem;
        padding-bottom: 0rem;
        margin-top: -4rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }}
    
    /* Make Language Switch Square and Bigger */
    div[data-testid="stSelectbox"] {{
        width: 6rem !important;
        margin-left: auto;
    }}
    div[data-testid="stSelectbox"] > div[data-baseweb="select"] > div {{
        height: 6rem !important;
        min-height: 6rem !important;
        border-radius: 12px !important;
    }}
    /* Target the text inside the selectbox aggressively */
    div[data-testid="stSelectbox"] [data-baseweb="select"] * {{
        font-size: 2rem !important;
        font-weight: 800 !important;
    }}
    
    /* Make ALL buttons identical in size */
    div[data-testid="stButton"] {{
        display: flex;
        justify-content: center;
    }}
    div[data-testid="stButton"] button {{
        width: 220px !important;
        height: 60px !important;
        font-size: 1.3rem !important;
        white-space: nowrap !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- DB Interactions ---
@st.cache_data(ttl=60)
def load_data(version="v1.0", lang="en"):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    
    q_col = 'question_text'
    if lang == 'ru': q_col = 'question_text_ru'
    elif lang == 'he': q_col = 'question_text_he'
    
    j_col = 'justification_quote'
    if lang == 'ru': j_col = 'justification_quote_ru'
    elif lang == 'he': j_col = 'justification_quote_he'

    questions_df = pd.read_sql_query(
        f"SELECT id, COALESCE({q_col}, question_text) as question_text, axis_id FROM dynamic_questionnaires WHERE questionnaire_version = '{version}'",
        conn
    )
    parties_df = pd.read_sql_query("SELECT id, name FROM parties_registry", conn)
    scores_df = pd.read_sql_query(
        f"SELECT party_id, question_id, score, COALESCE({j_col}, justification_quote) as justification_quote FROM party_simulations WHERE questionnaire_version = '{version}'",
        conn
    )
    axes_df = pd.read_sql_query("SELECT id, pole_minus_1, pole_plus_1 FROM axes_dictionary", conn)
    
    # Metadata for dashboard (Changed from sync_metadata to app_metadata to fix error)
    try:
        meta_df = pd.read_sql_query("SELECT key, value FROM app_metadata", conn)
        meta = dict(zip(meta_df.key, meta_df.value))
    except Exception:
        meta = {}

    conn.close()
    return questions_df, parties_df, scores_df, axes_df, meta

def save_metadata(key, value):
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS app_metadata (
                      key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute("INSERT OR REPLACE INTO app_metadata (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# --- Logic ---
def calculate_matches(user_scores, questions_df, parties_df, scores_df):
    results = []
    for _, party in parties_df.iterrows():
        party_id = party['id']
        party_scores = scores_df[scores_df['party_id'] == party_id]
        if party_scores.empty: continue
            
        distance = 0.0
        valid_qs = 0
        party_responses = {}
        
        for q_id, u_score in user_scores.items():
            ps_row = party_scores[party_scores['question_id'] == q_id]
            if not ps_row.empty:
                p_score = ps_row.iloc[0]['score']
                quote = ps_row.iloc[0]['justification_quote']
                distance += (u_score - p_score) ** 2
                valid_qs += 1
                party_responses[q_id] = {'score': p_score, 'quote': quote}
            
        if valid_qs > 0:
            max_dist = valid_qs * 4
            match_percentage = max(0, 100 - (sqrt(distance) / sqrt(max_dist) * 100))
            results.append({
                'party_id': party_id,
                'party_name': party['name'],
                'match_percentage': match_percentage,
                'responses': party_responses
            })
            
    results.sort(key=lambda x: x['match_percentage'], reverse=True)
    return results

def run_pipeline():
    try:
        subprocess.run(["python", "discovery/pipeline.py"], check=True, capture_output=True)
        subprocess.run(["python", "-m", "scoring.score_parties"], check=True, capture_output=True)
        save_metadata("last_scan_time", datetime.now().strftime("%H:%M:%S"))
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM parties_registry")
        count = c.fetchone()[0]
        try:
            old_count = int(pd.read_sql_query("SELECT value FROM app_metadata WHERE key='total_parties'", conn).iloc[0]['value'])
        except:
            old_count = 0
        added = count - old_count
        save_metadata("total_parties", str(count))
        save_metadata("added_parties", str(max(0, added)))
        conn.close()
        load_data.clear()
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Pipeline error: {e.stderr.decode()}")
        return False

# --- App ---
def main():
    if 'lang' not in st.session_state:
        st.session_state.lang = 'en'
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    
    t = load_locale(st.session_state.lang)
    
    # Hide sidebar via CSS (optional, but ensures it's gone)
    st.markdown("""
        <style>
            [data-testid="collapsedControl"] { display: none; }
            section[data-testid="stSidebar"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    
    inject_custom_css()
    
    header_container = st.container()
    with header_container:
        st.markdown("<span id='sticky-header'></span>", unsafe_allow_html=True)
        
        # cols: Title, Total Parties, Last Updated, Scan, Lang
        # Scan weight = 1.0, Total = 4.2+0.8+0.8+1+0.5 = 7.3 -> 1/7.3 = 13.7% width
        cols = st.columns([4.2, 0.8, 0.8, 1.0, 0.5], vertical_alignment="bottom")
        
        with cols[0]:
            st.markdown(f"<div style='font-size: 3rem; font-weight: 800; line-height: 1.1; margin-bottom: 0.5rem;'>{t.get('title', 'Where am I today on the Israeli political map?')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size: 1.3rem; margin-top:0.5rem;'>{t.get('subtitle', '')}</div>", unsafe_allow_html=True)
            
        try:
            _, _, _, _, meta = load_data(lang=st.session_state.lang)
            with cols[1]:
                st.metric("Total Parties", meta.get('total_parties', '0'), f"+{meta.get('added_parties', '0')}")
            with cols[2]:
                st.metric("Last Updated", meta.get('last_scan_time', 'N/A'))
        except Exception:
            pass

        with cols[3]:
            if st.button(t.get('scan_button', 'Scan News 🔄')):
                with st.spinner(t.get('scan_in_progress', 'Scanning...')):
                    if run_pipeline():
                        st.success(t.get('scan_complete', 'Done!'))
                        
        with cols[4]:
            new_lang = st.selectbox("Lang", ["en", "ru", "he"], index=["en", "ru", "he"].index(st.session_state.lang), label_visibility="collapsed")
            if new_lang != st.session_state.lang:
                st.session_state.lang = new_lang
                st.rerun()
            
        st.markdown("---")
    
    try:
        q_df, p_df, s_df, a_df, _ = load_data(lang=st.session_state.lang)
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return
        
    if q_df.empty:
        st.warning("No questions found. Please run Scan News first.")
        return
    
    # Main UI Layout
    col_main, col_chart = st.columns([3, 1])
    
    with col_main:
        st.markdown("### Interactive Dashboard")
        st.markdown("Fill out your stances in the tiles below to see live updates.")
        
        # Pagination Logic
        if 'page' not in st.session_state:
            st.session_state.page = 0
            
        items_per_page = 6
        start_idx = st.session_state.page * items_per_page
        end_idx = start_idx + items_per_page
        page_df = q_df.iloc[start_idx:end_idx]

        # Grid of questions (3 per row)
        cols_per_row = 3
        for i in range(0, len(page_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(page_df):
                    q = page_df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"**{q['question_text']}**")
                            
                            axis_info = a_df[a_df['id'] == q['axis_id']]
                            if not axis_info.empty:
                                p_minus = axis_info.iloc[0]['pole_minus_1']
                                p_plus = axis_info.iloc[0]['pole_plus_1']
                                st.caption(f"{p_minus} ⬅️ ➡️ {p_plus}")
                                
                            # Use a slider for immediate feedback
                            val = st.slider(
                                "Stance", min_value=-1.0, max_value=1.0, 
                                value=st.session_state.user_answers.get(q['id'], 0.0), 
                                step=0.1, key=f"q_{q['id']}_{st.session_state.lang}", 
                                label_visibility="collapsed"
                            )
                            st.session_state.user_answers[q['id']] = val
                            
        # Pagination Controls
        st.markdown("<br>", unsafe_allow_html=True)
        # Next weight = 1.5, Total = 3.5+1.5+1+1.5+3.5 = 11 -> 1.5/11 = 13.6% width
        # This makes Next and Scan columns exactly the same width on screen!
        pag_col1, pag_col2, pag_col3, pag_col4, pag_col5 = st.columns([3.5, 1.5, 1, 1.5, 3.5])
        with pag_col2:
            if st.session_state.page > 0:
                if st.button(t.get('prev_btn', '⬅️ Previous')):
                    st.session_state.page -= 1
                    st.rerun()
        with pag_col3:
            total_pages = (len(q_df) - 1) // items_per_page + 1
            st.markdown(f"<div style='text-align: center; color: #94a3b8; padding-top: 1rem;'>Page {st.session_state.page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with pag_col4:
            if end_idx < len(q_df):
                if st.button(t.get('next_btn', 'Next ➡️')):
                    st.session_state.page += 1
                    st.rerun()

    with col_chart:
        st.markdown("### Live Match Analysis")
        matches = calculate_matches(st.session_state.user_answers, q_df, p_df, s_df)
        
        if matches:
            top_party = matches[0]
            st.markdown(f"#### Top Match: {top_party['party_name']}")
            st.markdown(f"<h2 style='color:#22c55e;'>{top_party['match_percentage']:.1f}%</h2>", unsafe_allow_html=True)
            
            # Radar Chart
            categories = []
            user_vals = []
            party_vals = []
            
            for q_id, val in st.session_state.user_answers.items():
                q_row = q_df[q_df['id'] == q_id]
                if not q_row.empty:
                    q_text = str(q_row['question_text'].iloc[0])
                    short_q = q_text[:15] + "..." if len(q_text) > 15 else q_text
                else:
                    short_q = q_id[:8]
                    
                categories.append(short_q)
                user_vals.append(val)
                party_resp = top_party['responses'].get(q_id)
                party_vals.append(party_resp['score'] if party_resp else 0)
                
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=user_vals, theta=categories, fill='toself', name=t.get('you', 'You'), line=dict(color='#a855f7')))
            fig.add_trace(go.Scatterpolar(r=party_vals, theta=categories, fill='toself', name=top_party['party_name'], line=dict(color='#22c55e')))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[-1, 1], gridcolor='rgba(255,255,255,0.2)')),
                showlegend=True,
                legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#f8fafc'),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show other top matches
            st.markdown("#### Runners up")
            for m in matches[1:4]:
                st.markdown(f"{m['party_name']}: **{m['match_percentage']:.1f}%**")

if __name__ == "__main__":
    main()
