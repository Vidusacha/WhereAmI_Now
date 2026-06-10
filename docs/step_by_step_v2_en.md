# Step-by-Step Implementation Guide (V2)

This document provides a granular, technical step-by-step instruction set for migrating to the V2 architecture.

## Step 1: Initialize Database & Migrations
1. Configure `backend/database.py` with SQLAlchemy async engine connecting to PostgreSQL.
2. Initialize **Alembic** (`alembic init alembic`) to manage database migrations.
3. Generate the first migration script based on the models created (`axes`, `parties`, `questions`, `party_scores`, `scraped_documents`).
4. Apply migrations to the local Postgres container.

## Step 2: Build FastAPI CRUD Endpoints
1. Create `backend/api/routes/parties.py` to handle `GET /parties`, `POST /parties` (for manual additions), and `PUT /parties/{id}/approve`.
2. Create `backend/api/routes/axes.py` for Axis management.
3. Create `backend/api/routes/sources.py` to handle `POST /sources` for manual **Static Source URL** ingestion (e.g. gov.il links).
4. Hook these routes into `main.py`.
5. Test endpoints using Swagger UI (built into FastAPI at `/docs`).

## Step 3: AI Workers & The Fallback Cascade Scraper
1. Create `backend/services/scraper_service.py`. Implement the **Fallback Cascade Strategy**:
   - Check if URL is a PDF -> download and parse using `PyMuPDF`.
   - If HTML -> fetch via `requests` and parse with `BeautifulSoup`.
   - If blocked (403/Captcha) -> fallback to `Tavily` `/extract` endpoint to get clean Markdown.
2. Create `backend/services/ai_service.py` to interface with the local Ollama LLM.
3. Write strict prompts: *"Extract ONLY political parties, factions, or alliances. STRICTLY IGNORE government entities, ministries, military branches."*
4. Create background tasks (using FastAPI `BackgroundTasks`) so that scraping doesn't block API responses.

## Step 4: Reverse Axis Search Implementation
1. Create a function `generate_search_queries(axis_description)` in `ai_service.py`.
2. Integrate **Google Programmable Search Engine (PSE)** to accept these queries and return the Top 5 precise, high-trust URLs (e.g., from official party sites, Knesset, or major news outlets).
3. Pass these 5 URLs back to `scraper_service.py` (the Fallback Cascade) to extract the text.
4. LLM analyzes the extracted text to place parties on the axis (Score: -1 to 1) and saves to the database.

## Step 5: Flutter Admin Panel
1. Run `flutter create frontend` to scaffold the project.
2. Set up routing (e.g., `go_router`).
3. Build the `/admin` route with tabs for: **Pending Axes**, **Pending Parties**, and **Pending Questions**.
4. Create UI tables that fetch data from the FastAPI backend and display "Approve" / "Reject" buttons.

## Step 6: Flutter Public Questionnaire
1. Rebuild the logic from the Streamlit app in Dart.
2. Build the "Start Questionnaire" screen.
3. Calculate user distances using the same mathematical logic, but implemented on the client-side (Dart) or via a `/calculate` API endpoint.

## Step 7: Kubernetes Local Testing
1. Ensure `docker-compose.yml` mounts the codebase for live-reloading.
2. Build the Docker images for Backend and Frontend.
3. Apply the `k8s/` YAML files to a local cluster (like Docker Desktop K8s or Minikube) to ensure Traefik correctly routes `/api` traffic to Python and `/` traffic to Flutter.
