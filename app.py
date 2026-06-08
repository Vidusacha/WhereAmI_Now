import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import os
from math import sqrt

DB_PATH = 'database/whereami_core.db'

# --- Custom CSS for Premium Design ---
def inject_custom_css():
    st.markdown("""
    <style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark theme overrides */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    /* Glassmorphism Card Style */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Center aligning text in specific headers */
    h1 {
        text-align: center;
        background: -webkit-linear-gradient(45deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 10px;
    }
    .stButton>button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data(version="v1.0"):
    conn = sqlite3.connect(DB_PATH)
    
    # Load Questions
    questions_df = pd.read_sql_query(
        f"SELECT id, question_text, axis_id FROM dynamic_questionnaires WHERE questionnaire_version = '{version}'",
        conn
    )
    
    # Load Parties
    parties_df = pd.read_sql_query("SELECT id, name FROM parties_registry", conn)
    
    # Load Scores
    scores_df = pd.read_sql_query(
        f"SELECT party_id, question_id, score, justification_quote FROM party_simulations WHERE questionnaire_version = '{version}'",
        conn
    )
    
    # Load Axes mapping
    axes_df = pd.read_sql_query("SELECT id, pole_minus_1, pole_plus_1 FROM axes_dictionary", conn)
    
    conn.close()
    return questions_df, parties_df, scores_df, axes_df

def calculate_matches(user_scores, questions_df, parties_df, scores_df):
    """
    user_scores: dict {question_id: score}
    Returns a dataframe of party matches.
    """
    results = []
    
    for _, party in parties_df.iterrows():
        party_id = party['id']
        party_scores = scores_df[scores_df['party_id'] == party_id]
        
        if party_scores.empty:
            continue
            
        # Create party vector matching user questions
        distance = 0.0
        valid_qs = 0
        party_responses = {}
        
        for q_id, u_score in user_scores.items():
            ps_row = party_scores[party_scores['question_id'] == q_id]
            if not ps_row.empty:
                p_score = ps_row.iloc[0]['score']
                quote = ps_row.iloc[0]['justification_quote']
                
                # Euclidean distance squared
                distance += (u_score - p_score) ** 2
                valid_qs += 1
                party_responses[q_id] = {'score': p_score, 'quote': quote}
            
        if valid_qs > 0:
            # Max possible distance squared per question is 2^2 = 4
            max_dist = valid_qs * 4
            match_percentage = max(0, 100 - (sqrt(distance) / sqrt(max_dist) * 100))
            
            results.append({
                'party_id': party_id,
                'party_name': party['name'],
                'match_percentage': match_percentage,
                'responses': party_responses
            })
            
    # Sort by match descending
    results.sort(key=lambda x: x['match_percentage'], reverse=True)
    return results

def main():
    st.set_page_config(page_title="WhereAmI Now", page_icon="🧭", layout="centered", initial_sidebar_state="collapsed")
    inject_custom_css()
    
    st.markdown("<h1>🧭 WhereAmI Now?</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Discover which Israeli political party truly aligns with your views today, powered by real-time AI analysis.</p>", unsafe_allow_html=True)
    
    try:
        q_df, p_df, s_df, a_df = load_data()
    except Exception as e:
        st.error(f"Error loading database: {e}. Are you sure you are in the project root?")
        return
        
    if q_df.empty:
        st.warning("No questions found in the database. Please run Phase 3 first.")
        return
        
    # State management
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
        
    if not st.session_state.submitted:
        st.markdown("### Answer the following questions:")
        
        with st.form("questionnaire_form"):
            user_answers = {}
            
            for idx, q in q_df.iterrows():
                st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown(f"**{idx+1}. {q['question_text']}**")
                
                # Get pole text
                axis_info = a_df[a_df['id'] == q['axis_id']]
                if not axis_info.empty:
                    pole_m = axis_info.iloc[0]['pole_minus_1']
                    pole_p = axis_info.iloc[0]['pole_plus_1']
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"⬅️ {pole_m}")
                    with col2:
                        st.markdown(f"<div style='text-align: right;'><small>{pole_p} ➡️</small></div>", unsafe_allow_html=True)
                
                # Slider from -1.0 to 1.0
                val = st.slider("Your stance", min_value=-1.0, max_value=1.0, value=0.0, step=0.1, key=f"q_{q['id']}", label_visibility="collapsed")
                user_answers[q['id']] = val
                st.markdown("</div>", unsafe_allow_html=True)
                
            submit_btn = st.form_submit_button("Calculate My Match")
            
            if submit_btn:
                st.session_state.user_answers = user_answers
                st.session_state.submitted = True
                st.rerun()
                
    else:
        # Results View
        st.markdown("## 🏆 Your Top Matches")
        
        matches = calculate_matches(st.session_state.user_answers, q_df, p_df, s_df)
        
        if not matches:
            st.error("Not enough data to calculate matches.")
            if st.button("Start Over"):
                st.session_state.submitted = False
                st.rerun()
            return
            
        top_matches = matches[:5]
        
        for i, match in enumerate(top_matches):
            is_first = (i == 0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### #{i+1} {match['party_name']}")
            with col2:
                # Color code the percentage
                color = "#22c55e" if match['match_percentage'] >= 75 else "#eab308" if match['match_percentage'] >= 50 else "#ef4444"
                st.markdown(f"<h2 style='color: {color}; margin:0; text-align:right;'>{match['match_percentage']:.1f}%</h2>", unsafe_allow_html=True)
                
            # For the top match, show detailed breakdown
            if is_first:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("#### 🔍 Why did you match?")
                
                for q_id, user_val in st.session_state.user_answers.items():
                    party_resp = match['responses'].get(q_id)
                    if party_resp:
                        q_text = q_df[q_df['id'] == q_id].iloc[0]['question_text']
                        party_val = party_resp['score']
                        diff = abs(user_val - party_val)
                        
                        if diff < 0.5:
                            st.success(f"**Agree on:** {q_text}")
                            st.caption(f"*{party_resp['quote']}*")
                        elif diff > 1.0:
                            st.error(f"**Disagree on:** {q_text}")
                            st.caption(f"*{party_resp['quote']}*")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                with st.expander("View Details"):
                    st.markdown(f"The mathematical distance between your answers and {match['party_name']}'s simulated positions resulted in a {match['match_percentage']:.1f}% match.")
                    
            st.divider()
            
        if st.button("Take Test Again"):
            st.session_state.submitted = False
            st.rerun()

if __name__ == "__main__":
    main()
