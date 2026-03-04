# CLAUDE.md — ChefGPT MVP Specification

This document is the single source of truth for building **ChefGPT MVP**.
Core LLM: **Gemini 2.5 Flash** (free tier via Google AI Studio). Social/Grocery features use mock data.

---

# 1. Summary

ChefGPT MVP is a mobile AI cooking assistant focused on two real AI workflows:
- **Ingredient → Recipe generation** (text + photo input)
- **Meal planning + nutrition analysis**

Everything else (social feed, grocery shopping) is mocked for demo purposes.

---

# 2. Features & Implementation Status

## 2.1 AI Recipe Generation ✅ (real)
- User nhập nguyên liệu bằng text → Gemini 2.5 Flash gợi ý món.
- User chụp ảnh nguyên liệu → Gemini Vision nhận diện → gợi ý món.
- Trả về hướng dẫn nấu từng bước.
- Lọc theo sở thích: không cay, chay, ít dầu, v.v.

Endpoint: `POST /recipes/suggest`

## 2.2 Meal Plan + Nutrition ✅ (real)
- Tạo thực đơn theo tuần dựa trên mục tiêu (giảm cân, tăng cơ, eat clean...).
- Gemini 2.5 Flash sinh thực đơn và ước tính dinh dưỡng (calories, protein, carb, fat).

Endpoint: `POST /mealplan/generate`

## 2.3 Grocery List 🟡 (mock)
- Trả về danh sách mua sắm tĩnh từ mock data.
- Không gọi LLM, không tích hợp API siêu thị.

Endpoint: `GET /shopping-list/mock`

## 2.4 Social Feed 🟡 (mock)
- Feed bài đăng, like, comment từ hardcoded JSON.
- Không có realtime, không có user-generated content thật.

Endpoint: `GET /posts/mock`

---

# 3. Tech Stack (MVP)

## Mobile
- **Flutter** — cross-platform, 1 codebase
- State: **Riverpod**
- Networking: **Dio**
- Image: **image_picker**

## Backend
- **FastAPI** (Python)
- **SQLite** (local dev) → PostgreSQL khi scale
- **Supabase Auth** — xác thực người dùng

## AI Layer
- **Gemini 2.5 Flash** via `google-generativeai` SDK (free tier)
- Prompt engineering trực tiếp — không cần RAG, không cần vector DB ở MVP
- Vision: Gemini multimodal (nhận diện ảnh nguyên liệu, không cần CV model riêng)

## Infrastructure
- **Docker Compose** (local dev)
- Deploy: **Railway** hoặc **Render** (free tier)

---

# 4. Architecture (MVP)

```
Flutter App
    │
    ▼
FastAPI Backend
    ├── POST /recipes/suggest     → GeminiService (text + vision)
    ├── POST /mealplan/generate   → GeminiService
    ├── GET  /shopping-list/mock  → MockData
    └── GET  /posts/mock          → MockData
    │
    ▼
Supabase Auth + SQLite (lưu user history)
```

**Nguyên tắc**: Mọi AI call đều đi qua `GeminiService` để dễ swap model sau.

---

# 5. Directory Structure

```
chefgpt/
├── mobile/                  # Flutter app
│   ├── lib/
│   │   ├── features/
│   │   │   ├── recipe/
│   │   │   ├── meal_plan/
│   │   │   ├── grocery/     # mock
│   │   │   └── social/      # mock
│   │   ├── services/
│   │   └── main.dart
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   ├── recipes.py
│   │   │   ├── mealplan.py
│   │   │   ├── shopping.py  # mock
│   │   │   └── posts.py     # mock
│   │   ├── services/
│   │   │   └── gemini.py    # GeminiService (single AI entry point)
│   │   ├── models/
│   │   ├── mocks/           # JSON mock data
│   │   └── main.py
│   └── tests/
└── docs/
```

---

# 6. API Specification

### POST /recipes/suggest
```json
Request:  { "ingredients": ["cà chua", "trứng"], "filters": ["chay"] }
          or multipart/form-data with image
Response: { "dishes": [...], "instructions": {...} }
```

### POST /mealplan/generate
```json
Request:  { "goal": "eat_clean", "days": 7, "calories_target": 1800 }
Response: { "plan": [...], "nutrition_summary": {...} }
```

### GET /shopping-list/mock
```json
Response: { "items": [...] }  // hardcoded
```

### GET /posts/mock
```json
Response: { "posts": [...] }  // hardcoded
```

---

# 7. Database (MVP — minimal)

```
users           — id, email, created_at
profiles        — user_id, goal, dietary_prefs
recipe_history  — user_id, recipe_name, ingredients, created_at
meal_plans      — user_id, plan_json, created_at
```

Không có bảng `posts`, `embeddings`, `nutrition_db` ở MVP.

---

# 8. GeminiService — Core AI Logic

```python
# backend/app/services/gemini.py
import google.generativeai as genai

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def suggest_recipes(self, ingredients: list[str], filters: list[str]) -> dict: ...
    async def recognize_ingredients(self, image_bytes: bytes) -> list[str]: ...
    async def generate_meal_plan(self, goal: str, days: int, calories: int) -> dict: ...
```

---

# 9. Roadmap

## Phase 1 — MVP (hiện tại)
- [x] Flutter app skeleton + navigation
- [x] Supabase Auth (login/register)
- [x] GeminiService (text recipe + vision)
- [x] Recipe suggestion screen
- [x] Meal plan screen
- [x] Mock social feed + mock grocery list

## Phase 2 — Social & Grocery (real)
- Supabase Realtime cho social feed
- Shopping list tự sinh từ thực đơn

## Phase 3 — AI Automation
- Tích hợp API siêu thị (Bách Hóa Xanh, Winmart...)
- Agent cá nhân hoá theo sức khỏe
- Nâng cấp model nếu cần (Gemini Pro / Claude)

---

# 10. Instructions for Claude

Khi generate code cho project này, Claude phải:
1. Dùng **Gemini 2.5 Flash** làm LLM duy nhất — không dùng GPT hay Claude API.
2. Mọi AI call đi qua `GeminiService` — không gọi trực tiếp ở router.
3. Mock data đặt trong `/mocks/*.json` — tách biệt hoàn toàn khỏi business logic.
4. **Không implement** RAG, pgvector, Celery, Kubernetes ở giai đoạn này.
5. Code FastAPI phải có Pydantic models cho tất cả request/response.
6. Flutter dùng Riverpod cho state management.
7. Secrets trong `.env`, không hardcode API key.

---

# END
