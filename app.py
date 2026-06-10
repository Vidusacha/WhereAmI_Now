import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import subprocess
from math import sqrt
from datetime import datetime

DB_PATH = 'database/whereami_core.db'

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
    
    .stApp {{
        background-color: #0f172a;
        color: #f8fafc;
    }}
    
    .glass-card {{
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }}
    
    h1 {{
        text-align: center;
        background: -webkit-linear-gradient(45deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }}
    
    .subtitle {{
        text-align: center;
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
    </style>
    """, unsafe_allow_html=True)

# --- DB Interactions ---
@st.cache_data(ttl=60) # Cache clears every 60s to allow updates
def load_data(version="v1.0", lang="en"):
    conn = sqlite3.connect(DB_PATH)
    
    q_col = 'question_text'
    if lang == 'ru': q_col = 'question_text_ru'
    elif lang == 'he': q_col = 'question_text_he'
    
    j_col = 'justification_quote'
    if lang == 'ru': j_col = 'justification_quote_ru'
    elif lang == 'he': j_col = 'justification_quote_he'

    # Safely fallback to English if missing
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
    
    # Metadata for dashboard
    try:
        meta_df = pd.read_sql_query("SELECT key, value FROM sync_metadata", conn)
        meta = dict(zip(meta_df.key, meta_df.value))
    except sqlite3.OperationalError:
        meta = {}

    conn.close()
    return questions_df, parties_df, scores_df, axes_df, meta

def save_metadata(key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Ensure table exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS sync_metadata (
                      key TEXT PRIMARY KEY, value TEXT, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute("INSERT OR REPLACE INTO sync_metadata (key, value) VALUES (?, ?)", (key, value))
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
    # Execute the discovery pipeline and then scoring
    try:
        # Run discovery
        subprocess.run(["python", "discovery/pipeline.py"], check=True, capture_output=True)
        # Run scoring
        subprocess.run(["python", "-m", "scoring.score_parties"], check=True, capture_output=True)
        
        # Update metadata
        save_metadata("last_scan_time", datetime.now().strftime("%H:%M:%S"))
        # Get count
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM parties_registry")
        count = c.fetchone()[0]
        old_count = int(pd.read_sql_query("SELECT value FROM sync_metadata WHERE key='total_parties'", conn).iloc[0]['value'] if pd.read_sql_query("SELECT value FROM sync_metadata WHERE key='total_parties'", conn).shape[0] > 0 else 0)
        added = count - old_count
        save_metadata("total_parties", str(count))
        save_metadata("added_parties", str(max(0, added)))
        conn.close()
        
        # Clear cache to load new data
        load_data.clear()
        return True
    except subprocess.CalledProcessError as e:
        st.error(f"Pipeline error: {e.stderr.decode()}")
        return False

# --- App ---
def main():
    if 'lang' not in st.session_state:
        st.session_state.lang = 'en'
    
    st.set_page_config(page_title="WhereAmI Now", page_icon="🧭", layout="centered", initial_sidebar_state="expanded")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### Settings")
        new_lang = st.selectbox("Language", ["en", "ru", "he"], index=["en", "ru", "he"].index(st.session_state.lang))
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()
            
        t = load_locale(st.session_state.lang)
        
        st.markdown("---")
        if st.button(t.get('scan_button', 'Scan News')):
            with st.spinner(t.get('scan_in_progress', 'Scanning...')):
                success = run_pipeline()
                if success:
                    st.success(t.get('scan_complete', 'Done!'))
                    
        # Dashboard Metadata
        try:
            _, _, _, _, meta = load_data(lang=st.session_state.lang)
            last_time = meta.get('last_scan_time', 'N/A')
            total = meta.get('total_parties', '0')
            added = meta.get('added_parties', '0')
            
            st.info(t.get('last_updated', 'Updated at {time}').replace('{time}', last_time))
            st.caption(t.get('parties_listed', '{total} listed').replace('{total}', total))
            st.caption(t.get('parties_added', '{added} added').replace('{added}', added))
        except Exception:
            pass

    inject_custom_css()
    
    st.markdown(f"<h1>{t.get('title', 'WhereAmI Now?')}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='subtitle'>{t.get('subtitle', '')}</p>", unsafe_allow_html=True)
    
    try:
        q_df, p_df, s_df, a_df, _ = load_data(lang=st.session_state.lang)
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return
        
    if q_df.empty:
        st.warning("No questions found. Please run Scan News first.")
        return
        
    # State management
    if 'current_q' not in st.session_state:
        st.session_state.current_q = 0
        st.session_state.user_answers = {}
        st.session_state.submitted = False

    if not st.session_state.submitted:
        total_q = len(q_df)
        curr = st.session_state.current_q
        
        # Progress Bar
        progress_text = t.get('question_progress', 'Question {current} of {total}').replace('{current}', str(curr+1)).replace('{total}', str(total_q))
        st.progress((curr) / total_q, text=progress_text)
        
        q = q_df.iloc[curr]
        
        st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<h3>{q['question_text']}</h3>", unsafe_allow_html=True)
        
        axis_info = a_df[a_df['id'] == q['axis_id']]
        if not axis_info.empty:
            pole_m = axis_info.iloc[0]['pole_minus_1']
            pole_p = axis_info.iloc[0]['pole_plus_1']
            
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"⬅️ {pole_m}")
            with col2:
                align = "left" if st.session_state.lang == "he" else "right"
                st.markdown(f"<div style='text-align: {align};'><small>{pole_p} ➡️</small></div>", unsafe_allow_html=True)
        
        val = st.slider("Stance", min_value=-1.0, max_value=1.0, value=st.session_state.user_answers.get(q['id'], 0.0), step=0.1, key=f"q_{q['id']}_{st.session_state.lang}", label_visibility="collapsed")
        st.session_state.user_answers[q['id']] = val
        st.markdown("</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if curr > 0:
                if st.button(t.get('prev_btn', 'Previous')):
                    st.session_state.current_q -= 1
                    st.rerun()
        with col2:
            if curr < total_q - 1:
                if st.button(t.get('next_btn', 'Next')):
                    st.session_state.current_q += 1
                    st.rerun()
            else:
                if st.button(t.get('submit_btn', 'Submit')):
                    st.session_state.submitted = True
                    st.rerun()
                
    else:
        # Results View
        st.markdown(f"## {t.get('top_matches', 'Your Top Matches')}")
        matches = calculate_matches(st.session_state.user_answers, q_df, p_df, s_df)
        
        if not matches:
            st.error("Not enough data to calculate matches.")
            if st.button(t.get('start_over', 'Start Over')):
                st.session_state.submitted = False
                st.session_state.current_q = 0
                st.rerun()
            return
            
        top_matches = matches[:5]
        
        for i, match in enumerate(top_matches):
            is_first = (i == 0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### #{i+1} {match['party_name']}")
            with col2:
                color = "#22c55e" if match['match_percentage'] >= 75 else "#eab308" if match['match_percentage'] >= 50 else "#ef4444"
                align = "left" if st.session_state.lang == "he" else "right"
                st.markdown(f"<h2 style='color: {color}; margin:0; text-align:{align};'>{match['match_percentage']:.1f}%</h2>", unsafe_allow_html=True)
                
            if is_first:
                st.markdown("<div class='glass-card' style='text-align: left;'>", unsafe_allow_html=True)
                st.markdown(f"#### {t.get('why_matched', 'Why did you match?')}")
                
                for q_id, user_val in st.session_state.user_answers.items():
                    party_resp = match['responses'].get(q_id)
                    if party_resp:
                        q_text = q_df[q_df['id'] == q_id].iloc[0]['question_text']
                        party_val = party_resp['score']
                        diff = abs(user_val - party_val)
                        
                        if diff < 0.5:
                            st.success(f"**{t.get('agree_on', 'Agree on')}**: {q_text}")
                            st.caption(f"*{party_resp['quote']}*")
                        elif diff > 1.0:
                            st.error(f"**{t.get('disagree_on', 'Disagree on')}**: {q_text}")
                            st.caption(f"*{party_resp['quote']}*")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                with st.expander(t.get('view_details', 'View Details')):
                    desc = t.get('match_distance_desc', '').replace('{party}', match['party_name']).replace('{score}', f"{match['match_percentage']:.1f}")
                    st.markdown(desc)
                    
            st.divider()
            
        if st.button(t.get('start_over', 'Start Over')):
            st.session_state.submitted = False
            st.session_state.current_q = 0
            st.rerun()

if __name__ == "__main__":
    main()
