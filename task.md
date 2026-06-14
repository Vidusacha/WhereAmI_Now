# V2 Architecture Migration Tasks

- [x] **Step 1: Initialize Database & Migrations**
  - [x] Configure backend/database.py with SQLAlchemy async engine connecting to PostgreSQL.
  - [x] Initialize Alembic to manage database migrations.
  - [x] Generate the first migration script based on models.
  - [x] Apply migrations to the local Postgres container.

- [x] **Step 2: Build FastAPI CRUD Endpoints**
  - [x] Create backend/api/routes/parties.py to handle GET, POST, and PUT /approve.
  - [x] Create backend/api/routes/axes.py for Axis management.
  - [x] Create backend/api/routes/sources.py for manual Static Source URL ingestion.
  - [x] Hook these routes into main.py.
  - [x] Test endpoints using Swagger UI.

- [x] **Step 3: AI Workers & Scraper Data Persistence**
  - [x] Add ollama to separate Docker compose for local LLM running.
  - [x] Create backend/services/scraper_service.py (Orchestrator logic for search/download).
  - [x] Create backend/services/ai_service.py to interface with Ollama.
  - [x] Setup background task execution in FastAPI for scraping jobs.
  - [x] Ensure ScrapedDocuments persist to DB and map host directory /data to container to avoid data loss.

- [x] **Step 4: Reverse Axis Search Implementation**
  - [x] Implement generate_search_queries using Ollama.
  - [x] Implement Google PSE API call to get Top 5 URLs.
  - [x] Wire URLs to scraper_service.py for extraction.
  - [x] Ollama scores the extracted text and saves to party_scores.

- [x] **Step 5: Flutter Admin Panel**
  - [x] Scaffold Flutter web project.
  - [x] Build /admin route with Pending items UI.
  - [x] Build /system route with Docker, PostgreSQL, and Host Node monitoring.
  - [x] Integrate custom registry URI handlers for direct SSH, DBeaver, and filesystem access.
  - [x] Integrate aesthetic document views with document count and last updated dates.

- [ ] **Step 6: Flutter Public Questionnaire**
  - [ ] Rebuild Streamlit logic in Dart.
  - [ ] Connect client-side to FastAPI.

- [ ] **Step 7: Kubernetes Local Testing**
  - [ ] Build final images.
  - [ ] Route traffic using Traefik via ingress.yaml.

- [x] **Step 8: UX & Design Documentation**
  - [x] Create and maintain design.md to dictate the UI/UX System Dashboard architecture.
  - [x] Improve Admin Dashboard aesthetics (Wrap layout, spacing, shadow box design).
