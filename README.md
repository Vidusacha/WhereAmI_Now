# WhereAmI_Now (Antigravity 2.0)

A dynamic, zero-hardcode system for tracking ideological shifts in the political landscape using LLMs.

## Overview
WhereAmI_Now aggregates daily news, discovers new political/social dividing lines (axes), extracts party statements, and generates dynamic questionnaires. Users can then find their position on the political map based on the most up-to-date data.

## Features
- **Temporal Tracking:** Logs historical data to track "Party Drift".
- **Dynamic Axes & Questionnaires:** No hardcoded questions. The system discovers what is relevant *today*.
- **Local & Cloud LLMs:** Uses local models via LM Studio (Mistral) for text analysis, and Gemini API for translations and RSS discovery.

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vidusacha/WhereAmI_Now.git
   cd WhereAmI_Now
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   - Create a `.env` file based on `.env.example` or just put your keys in `.env`:
   ```env
   GEMINI_API_KEY="your-gemini-api-key"
   GEMINI_MODEL="gemini-1.5-flash"
   LM_STUDIO_BASE_URL="http://localhost:1234/v1"
   ```

4. **Initialize Database:**
   ```bash
   python database/init_db.py
   python database/update_phase2.py
   ```

5. **Run Daily Discovery Pipeline:**
   ```bash
   python discovery/pipeline.py
   ```
