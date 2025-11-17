# CLAUDE.md — ChefGPT System Specification

This document provides a complete specification and technical understanding of the **ChefGPT** mobile application so that Claude can assist in building the full project (frontend + backend + AI agents + data pipelines).

---

# 1. Summary
ChefGPT is a mobile AI-powered cooking and nutrition assistant. It integrates:
- **LLM (GPT-4.1 or Claude)** for reasoning, recipe generation, nutrition advice.
- **Vision models** for ingredient detection.
- **RAG** for retrieving structured recipe + nutrition data.
- **Mobile app** (Flutter or React Native) as core interface.
- **Backend** (FastAPI) for business logic.
- **Supabase** or **Firebase** for auth, storage, realtime features.

Claude should understand this entire system to generate code components, API handlers, data schemas, RAG pipelines, UI, and architecture.

---

# 2. Core Features

## 2.1 AI Chatbot (Main Interface)
The chatbot performs:
- Recipe suggestions from **ingredients text** input.
- Recipe suggestions from **ingredient photos**.
- Suggestions from **mood / constraints** (“món ít calo”, “món nước”, “món không cay”).
- Nutrition advice (“Tôi có nên bỏ bữa sáng?”, “Trứng + cà chua OK không?”).
- Transform recipes (“phiên bản healthy”, “phiên bản rẻ hơn”).

Backend: `/chat/query` → LLM + tools.

## 2.2 Recipe Engine
- Parse ingredients.
- Query RAG recipes.
- Match available ingredients.
- Show missing ingredients.
- Provide step-by-step cooking instructions.
- Optional: generate or fetch demo videos.

## 2.3 Vision Ingredient Recognition
- Upload image → detect ingredients.
- Model option:
  - LLM Vision
  - YOLOv8 custom food model

Endpoint: `/ingredients/recognize`.

## 2.4 Meal Plan Generator
- Weekly/daily plans.
- Calories + macro estimation.
- Shopping list auto-generation.

Endpoint: `/mealplan/generate`.

## 2.5 Social Feed
Users can:
- Post recipes.
- Upload images/videos.
- Like/comment/bookmark.

Real-time updates via Supabase Realtime.

## 2.6 Shopping List
- AI-generated lists.
- Manual creation.
- Integration with supermarket APIs (future).

---

# 3. Tech Stack

## Frontend
- **Flutter (recommended)**
  - State: Riverpod / Bloc
  - Networking: Dio
  - Image: Image Picker

Alternative: **React Native**.

## Backend
- **FastAPI** (Python)
  - Pydantic models
  - PostgreSQL ORM (SQLModel / SQLAlchemy)
  - Task queue optional: Celery / RQ

## Database
- **PostgreSQL + pgvector** for embeddings
- **Supabase Auth**
- **Supabase Storage**

## AI Layer
- GPT-4.1 (OpenAI)
- Claude 3.5 Sonnet for generation/analysis
- Vision models
- Embeddings (OpenAI/text-embedding-3-large)

## RAG
- Store recipes, nutrition data, ingredient knowledge.
- Vector search → retrieve context for LLM.

---

# 4. System Architecture (Summary)
- Mobile App → FastAPI backend.
- Backend communicates with:
  - Auth (Supabase)
  - DB (PostgreSQL)
  - Storage (Supabase)
  - LLMs (GPT, Claude)
  - Vision Models
  - RAG vector store

---

# 5. Directory Structure (Recommended)
```
chefgpt/
├── mobile/ (Flutter or RN)
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── llm/
│   │   ├── rag/
│   │   └── utils/
│   ├── scripts/
│   └── tests/
├── data/
├── docs/
└── infra/
```

---

# 6. API Specification
A full OpenAPI file is available in `chefgpt_openapi.yaml`. Claude can use it to generate:
- FastAPI routers
- Pydantic request/response models
- Frontend service classes

Main endpoints:
- `/auth/*`
- `/recipes/*`
- `/ingredients/recognize`
- `/chat/query`
- `/mealplan/generate`
- `/shopping-list/*`
- `/posts/*`

---

# 7. Database (ERD)
Key tables:
- `users`, `profiles`
- `recipes`, `ingredients`, `recipe_ingredients`
- `posts`, `comments`, `likes`
- `meal_plans`, `meal_items`
- `shopping_lists`, `shopping_items`
- `nutrition_db`
- `embeddings`

Refer to ERD image provided earlier.

---

# 8. LLM Agent Logic
Claude should implement tools for:

### 8.1 Tools
- `search_recipe`
- `match_ingredients`
- `generate_meal_plan`
- `estimate_nutrition`
- `vision_recognize`

### 8.2 Agent Workflow
Example for recipe suggestion:
```
User input → LLM parse → detect mode
IF ingredients → ingredient matcher → RAG search → LLM re-rank
IF dish name → direct fetch → enrich
IF preference request → classify → filter recipes → suggest
```

---

# 9. Roadmap (Dev-focused)
## Phase 1 — Core (2 months)
- Auth
- Chatbot base
- Ingredient recognition
- Recipe engine MVP
- Shopping list MVP
- Backend + DB setup

## Phase 2 — Productization (3–4 months)
- Social feed
- Meal plan
- Nutrition system
- Profile personalization
- RAG v1

## Phase 3 — Advanced AI (6 months)
- Mood-based cooking
- Nutrition optimization algorithms
- Budget-based cooking
- Voice cooking assistant

---

# 10. Instructions for Claude
Claude should now:
1. Be able to generate **full backend code** based on FastAPI.
2. Generate **Flutter app structure + screens**.
3. Create **RAG pipeline** (embedding + DB schema + query code).
4. Implement **Vision pipeline**.
5. Assist in optimizing architecture.
6. Create deployment configs (Docker, Supabase configs).
7. Follow this document as the single source of truth.

If the user requests code, Claude should:
- follow the architecture above
- generate idiomatic, production-quality code
- ensure consistency with APIs, DB models, and flows defined here.

---

# END

