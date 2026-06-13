# WhereAmI Now: UI/UX Design System & Aesthetics

## Overview
The WhereAmI Now Admin Dashboard is built using **Flutter Web**. The primary goal is to maintain a clean, modern, and highly readable "material" interface tailored for data-heavy monitoring and administration tasks.

## Color Palette
- **Primary:** Deep Purple / Indigo (`Colors.deepPurple` for global accents)
- **Backgrounds:** Off-white (`Colors.grey.shade50`) for the scaffold background to reduce eye strain, while keeping cards pure white (`Colors.white`) for maximum contrast and elevation.
- **Success/Online:** Green (`Colors.green` and `Colors.green.shade100`) for active states, running containers, and online statuses.
- **Error/Offline:** Red (`Colors.red` and `Colors.red.shade100`) for disconnected nodes, failed fetch requests, and offline statuses.
- **Warning/Pending:** Orange (`Colors.orange` and `Colors.orange.shade100`) for items pending review or missing dependencies (e.g. models not downloaded).

## Layout & Structure
### Navigation
A left-side `NavigationRail` is used on wide screens (desktop) for quick access to main routes:
1. **Entities:** Management of political figures/entities.
2. **Entity Types:** Categorization of entities.
3. **Axes:** Political axes mapping.
4. **Questions:** Questionnaire generation.
5. **Documents:** Scraped/Ingested documents.
6. **System:** Dashboard for infrastructure monitoring (Docker, Host Node, DB, Local LLMs).

### System Dashboard
The System Dashboard is structured using a responsive grid-like system (`Wrap` widget) for high-level monitoring cards:
1. **Local Model Status:** Monitors Ollama/Qwen availability and loaded models.
2. **Host Node:** Displays live CPU, RAM, and Disk metrics of the underlying server.
3. **PostgreSQL Database:** Displays live status and storage footprint.

Beneath the vital cards, a full-width **Docker Containers** table provides granular insight into the microservices (CPU, Mem, Status).

## Interactivity & Protocols
To bridge the gap between the isolated browser sandbox and the local developer environment, the UI leverages custom URI handlers via the Windows Registry:
- `whereami-ssh://`: Spawns a native PowerShell interactive terminal directly connected to the specified Docker container via `docker exec`.
- `whereami-dbeaver://`: Launches the local DBeaver GUI pre-configured to inspect the database.
- `whereami-folder://`: Opens Windows Explorer directly to the downloaded/scraped documents folder.
- `whereami-ollamalog://`: Opens the local Ollama server logs in Notepad for debugging.

## Typography
Uses the standard Roboto font (Flutter's default) with distinct typography hierarchy:
- **Headers:** 20-22pt, `FontWeight.bold`
- **Body:** 14-16pt for readability
- **Meta/Tags:** 12-14pt, often styled with chips or colored backgrounds.

## Maintenance
This document should be updated whenever new major UI components or navigation routes are introduced to the Flutter application.
