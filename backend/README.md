# ChefGPT Backend API

FastAPI backend cho **ChefGPT** — trợ lý nấu ăn và dinh dưỡng AI.

- **AI**: Gemini 2.5 Flash (Google AI Studio — free tier)
- **Database**: SQLite (local dev) — không cần cài PostgreSQL
- **Auth**: JWT tự quản lý (python-jose + passlib)
- **Cache**: Redis (optional — fallback in-memory nếu không có Redis)

---

## Tính năng

| Tính năng | Endpoint | Chi tiết |
|-----------|----------|---------|
| Gợi ý món ăn | `POST /recipes/suggest` | Gemini + RAG community recipes + Persona + Cache |
| Nhận dạng nguyên liệu | `POST /ingredients/recognize` | Gemini Vision |
| Chat hỏi đáp | `POST /chat/query` | Gemini + Persona + Memory injection |
| Tạo thực đơn | `POST /mealplan/generate` | Gemini + Multi-persona + Cache |
| AI Persona | `GET/POST/PUT/DELETE /personas` | 6 system personas + custom personas |
| User Memory | `GET/POST/DELETE /memory/me` | Auto-extract + inject vào AI |
| Feed cộng đồng | `GET /posts/mock` | Mock JSON |
| Danh sách mua sắm | `GET /shopping-list/mock` | Mock JSON |

---

## Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| Framework | FastAPI 0.109+ |
| Database | SQLite + aiosqlite (async) |
| ORM | SQLModel (SQLAlchemy 2.0) |
| Migrations | Alembic |
| Auth | JWT — python-jose + passlib[bcrypt==3.2.2] |
| AI | google-genai (Gemini 2.5 Flash) |
| Cache | Redis (redis==5.0.1) |
| Embeddings | Gemini text-embedding-004 + numpy cosine sim |
| Logging | loguru + LoggingMiddleware |
| Python | 3.11+ (conda env: `ChefGPT`) |

---

## Cấu trúc thư mục

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py            # Settings từ .env
│   │   ├── database.py          # SQLite async engine + session
│   │   └── security.py          # JWT helpers
│   ├── models/
│   │   ├── user.py              # User, UserPersonaSetting
│   │   ├── chat.py              # ChatSession, ChatMessage
│   │   ├── meal_plan.py         # MealPlan
│   │   ├── persona.py           # CustomPersona
│   │   └── memory.py            # UserMemory
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── persona.py           # PersonaListItem, CreatePersonaRequest, ...
│   │   └── memory.py            # MemoryResponse, AddMemoryRequest, ...
│   ├── routers/
│   │   ├── auth.py              # /auth/*
│   │   ├── recipes.py           # /recipes/*
│   │   ├── vision.py            # /ingredients/recognize
│   │   ├── chat.py              # /chat/* (+ background memory extraction)
│   │   ├── meal_plan.py         # /mealplan/*
│   │   ├── personas.py          # /personas/* (system + custom CRUD)
│   │   ├── memory.py            # /memory/*
│   │   ├── social.py            # /posts/mock
│   │   └── shopping.py          # /shopping-list/mock
│   ├── services/
│   │   ├── llm/
│   │   │   ├── base_llm.py      # Abstract BaseLLM
│   │   │   ├── gemini_llm.py    # GeminiLLM (default)
│   │   │   ├── openai_llm.py    # OpenAILLM
│   │   │   └── anthropic_llm.py # AnthropicLLM
│   │   ├── persona_service.py   # Load + serve system persona JSONs
│   │   ├── persona_context.py   # Resolve PersonaContext per-request
│   │   ├── memory_service.py    # Extract + cache + inject user memory
│   │   ├── rag.py               # Semantic search (embeddings + cosine)
│   │   ├── cache.py             # Redis cache helpers
│   │   └── key_manager.py       # API key rotation (round-robin)
│   ├── personas/                # 6 system persona JSON configs
│   │   ├── asian_chef.json
│   │   ├── european_chef.json
│   │   ├── nutrition_expert.json
│   │   ├── vegan_chef.json
│   │   ├── home_chef.json
│   │   └── fitness_coach.json
│   ├── mocks/
│   │   ├── posts.json
│   │   ├── shopping.json
│   │   └── recipes.json         # 30 Vietnamese community recipes (RAG source)
│   └── main.py
├── alembic/
│   ├── versions/
│   │   ├── 001_initial.py
│   │   ├── 002_add_persona_settings.py
│   │   ├── 003_add_user_memories.py
│   │   └── 004_add_custom_personas.py
│   └── env.py
├── .env                         # Secrets (không commit)
├── .env.example
└── requirements.txt
```

---

## Cài đặt và chạy

### Yêu cầu

- [Anaconda](https://www.anaconda.com/) hoặc Python 3.11+
- Gemini API Key — lấy miễn phí tại [aistudio.google.com](https://aistudio.google.com/)
- Redis (optional) — nếu không có, cache fallback in-memory

### Bước 1 — Tạo conda environment

```bash
conda create -n ChefGPT python=3.11 -y
conda activate ChefGPT
```

### Bước 2 — Cài dependencies

```bash
cd backend
pip install -r requirements.txt
```

> **Lưu ý**: `passlib==1.7.4` yêu cầu `bcrypt==3.2.2`. bcrypt 4.x sẽ lỗi.

### Bước 3 — Cấu hình môi trường

```bash
cp .env.example .env
```

Các biến bắt buộc:

```env
GEMINI_API_KEY=AIza...           # Lấy từ Google AI Studio
JWT_SECRET_KEY=your-secret-key   # Chuỗi ngẫu nhiên bất kỳ
```

Các biến tùy chọn:

```env
DATABASE_URL=sqlite+aiosqlite:///./chefgpt.db
REDIS_URL=redis://localhost:6379
LLM_PROVIDER=gemini              # gemini | openai | anthropic
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

> SQLite DB (`chefgpt.db`) tự tạo khi khởi động. Alembic migrations chạy tự động qua lifespan.

### Bước 4 — Khởi động server

```bash
# Windows (conda env ChefGPT)
/d/Anaconda/envs/ChefGPT/python.exe -m uvicorn app.main:app --reload

# Mac/Linux
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server: `http://localhost:8000` | Docs: `http://localhost:8000/docs`

---

## API Reference

### Auth

```
POST /auth/signup     Đăng ký tài khoản mới
POST /auth/login      Đăng nhập → access_token + refresh_token
POST /auth/refresh    Làm mới access_token
POST /auth/logout     Đăng xuất
```

`access_token` hết hạn sau **1 giờ**. `refresh_token` hết hạn sau **7 ngày**.

---

### Personas

```
GET    /personas              Danh sách tất cả (system + custom của user)
GET    /personas/{id}         Chi tiết 1 persona
POST   /personas              Tạo custom persona mới (auth required)
PUT    /personas/{id}         Cập nhật custom persona (chỉ owner)
DELETE /personas/{id}         Xóa custom persona (chỉ owner)
GET    /personas/me           Persona đang active của user
PUT    /personas/me           Chọn persona + optional prompt overrides
DELETE /personas/me/overrides Xóa custom overrides, về mặc định
```

**6 System Personas** (`is_system=true`, không thể sửa/xóa):

| ID | Tên | Icon |
|----|-----|------|
| `asian_chef` | Đầu bếp Á *(default)* | 🍜 |
| `european_chef` | Đầu bếp Âu | 🥐 |
| `nutrition_expert` | Chuyên gia Dinh dưỡng | 🔬 |
| `vegan_chef` | Đầu bếp Chay | 🌱 |
| `home_chef` | Đầu bếp Gia đình | 🏠 |
| `fitness_coach` | Fitness Coach | 💪 |

**Custom Personas**: ID dạng `custom_{name_slug}_{uuid[:6]}`, VD: `custom_dau-bep-mien-trung_a1b2c3`

```json
// POST /personas
{
  "name": "Đầu bếp Miền Trung",
  "description": "Chuyên gia ẩm thực Huế, Đà Nẵng, Hội An",
  "icon": "🌶️",
  "color": "#EF4444",
  "system_prompt": "Bạn là ChefGPT — chuyên gia ẩm thực miền Trung...",
  "recipe_prefix": "Ưu tiên các món đặc sản miền Trung...",
  "meal_plan_prefix": "Tạo thực đơn theo phong cách ẩm thực miền Trung...",
  "cuisine_filters": ["vietnamese", "central_vietnamese"],
  "quick_actions": ["Công thức bún bò Huế chuẩn vị", "Cách làm bánh xèo miền Trung"],
  "is_public": true
}
```

---

### AI — Gợi ý món *(~30–120 giây)*

```
POST /recipes/suggest
Authorization: Bearer <access_token>
```

```json
// Request
{
  "ingredients": ["trứng", "cà chua", "hành lá"],
  "filters": ["ít dầu"],
  "persona_id": "asian_chef"    // optional — override persona
}
```

Cache: `hash(sorted(ingredients) + sorted(filters) + persona_id)`, TTL 60 phút.

---

### AI — Nhận dạng nguyên liệu *(Gemini Vision)*

```
POST /ingredients/recognize
Content-Type: multipart/form-data
Form field: image (JPG/PNG)
```

---

### AI — Chat *(~3–10 giây)*

```
POST /chat/query
```

```json
// Request
{
  "message": "Gợi ý bữa sáng cho người bận rộn",
  "session_id": null,           // null = tạo session mới
  "persona_id": "home_chef"     // optional
}
```

**Memory injection**: Memory của user được inject vào system_prompt mỗi lần chat.
**Background extraction**: Sau khi trả response, background task extract facts từ tin nhắn và lưu vào `user_memories`.

```
GET /chat/history   Lịch sử chat phân theo session
```

---

### AI — Tạo thực đơn *(~60–120 giây)*

```
POST /mealplan/generate
```

```json
// Request
{
  "goal": "weight_loss",
  "days": 7,
  "calories_target": 1800,
  "persona_ids": ["nutrition_expert", "fitness_coach"],  // array — multi-persona
  "user_note": "Dị ứng hải sản, thích món Việt"          // optional free-text
}
```

| `goal` | Ý nghĩa |
|--------|---------|
| `eat_clean` | Ăn sạch, lành mạnh |
| `weight_loss` | Giảm cân |
| `muscle_gain` | Tăng cơ |
| `keto` | Keto (ít carb) |
| `maintenance` | Duy trì cân nặng |

**Cache logic**:
- Không có `user_note` → cache, TTL 30 phút
- Có `user_note` → **không cache** (free-text, hit rate ~0)
- `persona_ids` được sort trước khi hash → `["A","B"]` == `["B","A"]`

```
GET /mealplan   Danh sách thực đơn đã lưu của user
```

---

### Memory

```
GET    /memory/me           Xem tất cả memory + context_preview
POST   /memory/me           Thêm memory thủ công
DELETE /memory/me/{id}      Xóa 1 memory (soft delete)
DELETE /memory/me           Xóa toàn bộ memory
GET    /memory/categories   Danh sách 6 categories với icon/label
```

**6 Categories**:

| ID | Icon | Label |
|----|------|-------|
| `dietary` | 🚫 | Chế độ ăn (dị ứng, kiêng khem) |
| `preference` | ✅ | Sở thích (loại món, hương vị) |
| `aversion` | ❌ | Không thích |
| `goal` | 🎯 | Mục tiêu (giảm cân, tăng cơ) |
| `constraint` | ⚠️ | Ràng buộc (thời gian, ngân sách) |
| `context` | 📝 | Thông tin khác (gia đình, lịch sinh hoạt) |

```json
// POST /memory/me
{ "category": "dietary", "key": "allergy", "value": "hải sản và tôm" }
```

---

### Mock

```
GET /posts/mock          5 bài đăng mẫu (không cần auth)
GET /shopping-list/mock  Danh sách mua sắm mẫu (không cần auth)
```

---

## LLM Provider

Đổi provider bằng biến môi trường `LLM_PROVIDER`:

```env
LLM_PROVIDER=gemini      # mặc định
LLM_PROVIDER=openai      # cần OPENAI_API_KEY
LLM_PROVIDER=anthropic   # cần ANTHROPIC_API_KEY
```

Tất cả provider đều implement `BaseLLM` với 4 methods:
- `suggest_recipes(ingredients, filters, persona)`
- `generate_meal_plan(goal, days, calories, persona, user_note)`
- `chat(message, history, persona)`
- `extract_memory_facts(user_message)` — dùng riêng cho background task

---

## Biến môi trường đầy đủ

Xem `.env.example` để biết tất cả biến. Bắt buộc:

```env
GEMINI_API_KEY=AIza...
JWT_SECRET_KEY=your-random-secret-32-chars
DATABASE_URL=sqlite+aiosqlite:///./chefgpt.db
```

---

## Tài liệu API

| URL | Mô tả |
|-----|-------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |

## Testing với Postman

1. Import `ChefGPT.postman_collection.json` vào Postman
2. Chạy **Login** → token tự lưu vào `{{access_token}}`
3. **Settings → Request timeout → 180000 ms** (AI endpoints mất 30–120s)
4. Xem section descriptions trong collection để biết flow test từng tính năng

---

## Lưu ý phát triển

- **AI chậm**: Gemini 2.5 Flash thinking mode — 30–120s cho recipe/mealplan. Chat ~5s.
- **bcrypt**: Dùng `bcrypt==3.2.2`, không dùng 4.x (incompatible với passlib 1.7.4).
- **Gemini SDK**: Dùng `google-genai` (mới), không dùng `google-generativeai` (deprecated).
- **Background tasks**: Memory extraction chạy sau khi response đã gửi — dùng `async_session_maker()` riêng.
- **Migrations**: Alembic chạy tự động khi server khởi động (`lifespan`).
