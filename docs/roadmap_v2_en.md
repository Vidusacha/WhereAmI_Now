# WhereAmI Project Roadmap (V2)

This roadmap outlines the high-level phases to transform the prototype into a production-ready, scalable AI platform.

## Phase 1: Foundation & Core Engine 🛠️
* **Goal:** Establish a robust, scalable backend infrastructure.
* **Key Deliverables:**
  * Deploy Kubernetes (K8s) architecture locally (Traefik, Postgres).
  * Build the FastAPI backend shell.
  * Create the new SQLAlchemy database schema with the `pending_ai_proposal` approval workflow.

## Phase 2: The AI Discovery Pipeline 🤖
* **Goal:** Automate the gathering and processing of political data with a highly cost-efficient extraction cascade.
* **Key Deliverables:**
  * Implement the **Fallback Cascade Strategy** for token saving: Wikipedia/Knesset APIs -> Direct PDF Download (PyMuPDF) -> Basic HTML Scraper (BeautifulSoup) -> Tavily `/extract` (Fallback for protected sites).
  * Develop the "Axis Discovery" worker (LLM reads news, suggests new political axes).
  * Develop the "Party Discovery" worker (Strictly filtering out ministries/government entities using open data/APIs).
  * Implement **Static Source URL Ingestion** (allowing manual submission of direct links, e.g., to specific datasets or manifestos).
  * Setup local offline storage for scraped documents (ready for future AWS S3 migration).

## Phase 3: Cross-Platform Frontend (Flutter) 📱
* **Goal:** Build a unified user interface for Web and Mobile.
* **Key Deliverables:**
  * Initialize the Flutter project.
  * Build the Admin Dashboard (for reviewing and approving AI-proposed axes, parties, and questions).
  * Rebuild the public-facing "Political Map" questionnaire UI.

## Phase 4: Reverse Axis Search & AI Question Generation 🔍
* **Goal:** Deepen the AI's understanding of the political landscape efficiently.
* **Key Deliverables:**
  * Implement "Reverse Search": AI generates search queries for an axis, **Google PSE** fetches precise high-trust URLs, and the Fallback Cascade extracts the content.
  * AI evaluates extracted markdown to place parties on axes (Scores from -1 to 1).
  * Automate questionnaire generation based on newly discovered axes.

## Phase 5: Production Launch & Scaling 🚀
* **Goal:** Go live.
* **Key Deliverables:**
  * Migrate local offline storage to AWS S3 / MinIO.
  * Deploy the Kubernetes cluster to a cloud provider (e.g., DigitalOcean, AWS, GCP).
  * Release the Web version.
  * Prepare the Android (.apk) build from the exact same Flutter codebase.
