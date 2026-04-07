# ChefGPT — AI Cooking & Nutrition Assistant

Mobile app trợ lý nấu ăn và dinh dưỡng AI, powered by **Gemini 2.5 Flash**.

## Features

| Feature | Status | Mô tả |
|---------|--------|-------|
| AI Recipe Suggestion | ✅ Real | Nhập nguyên liệu (text hoặc ảnh) → Gemini gợi ý 3 món |
| Ingredient Recognition | ✅ Real | Chụp ảnh nguyên liệu → Gemini Vision nhận diện tự động |
| Meal Plan Generator | ✅ Real | Tạo thực đơn tuần theo mục tiêu (giảm cân, tăng cơ, eat clean...) |
| Nutrition Chat | ✅ Real | Chat với AI về dinh dưỡng và công thức nấu ăn |
| AI Persona System | ✅ Real | Chọn phong cách AI (Đầu bếp Á, Âu, Dinh dưỡng, Chay, Gia đình, Fitness) |
| Custom Personas | ✅ Real | Tạo và cấu hình persona riêng với prompts tùy chỉnh |
| User Memory | ✅ Real | AI tự học và ghi nhớ dị ứng, sở thích, mục tiêu của từng user |
| Community RAG | ✅ Real | Gợi ý món dựa trên 30 công thức cộng đồng (semantic search) |
| Grocery Shopping | 🟡 Mock | Danh sách mua sắm tĩnh từ mock data |
| Social Feed | 🟡 Mock | Feed bài đăng, like, comment từ hardcoded JSON |

## Tech Stack

**Mobile**: Flutter + Riverpod + Dio + GoRouter

**Backend**: FastAPI + SQLite + JWT Auth

**AI**: Gemini 2.5 Flash (text + vision, free tier via Google AI Studio)

**Cache**: Redis (recipes TTL 60 min, meal plans TTL 30 min, memory TTL 10 min)

**Search**: RAG với Gemini text-embedding-004 + cosine similarity

## Architecture

```
Flutter App
    │
    ▼
FastAPI Backend (Python)
    ├── POST /recipes/suggest       → GeminiLLM + RAG + Persona + Memory + Cache
    ├── POST /ingredients/recognize → GeminiLLM (vision)
    ├── POST /mealplan/generate     → GeminiLLM + Persona (multi) + Memory + Cache
    ├── POST /chat/query            → GeminiLLM + Persona + Memory + Background extraction
    ├── GET  /personas              → PersonaService (system) + DB (custom)
    ├── POST /personas              → Tạo custom persona
    ├── GET  /memory/me             → User memory management
    ├── GET  /posts/mock            → Mock JSON
    └── GET  /shopping-list/mock    → Mock JSON
    │
    ▼
SQLite (local) — tự tạo khi khởi động
Redis (cache + key rotation)
```

## Quick Start

### Backend

```bash
# 1. Tạo conda environment
conda create -n ChefGPT python=3.11 -y
conda activate ChefGPT
pip install -r backend/requirements.txt

# 2. Cấu hình .env
cp backend/.env.example backend/.env
# Điền GEMINI_API_KEY vào backend/.env
# Lấy API key miễn phí: https://aistudio.google.com

# 3. Chạy server (Windows)
cd backend
/d/Anaconda/envs/ChefGPT/python.exe -m uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Mobile

```bash
cd mobile
flutter pub get

# Android emulator / thiết bị thật
flutter run

# Flutter Web — dùng bất kỳ port nào còn trống (CORS backend cho phép mọi port localhost)
flutter run -d chrome --web-port 3001
# hoặc để Flutter tự chọn port trống
flutter run -d chrome --web-port 0
```

**Backend URL theo môi trường** (`mobile/lib/core/constants/app_constants.dart`):
- Android emulator: `http://10.0.2.2:8000`
- Android thật (cùng WiFi): `http://<IP_PC>:8000`
- iOS simulator: `http://localhost:8000`
- Flutter Web: `http://localhost:8000` (CORS cho phép `localhost:3000`)

## Environment Variables

```env
# Bắt buộc
GEMINI_API_KEY=AIza...             # https://aistudio.google.com
JWT_SECRET_KEY=your-secret-here

# Tùy chọn (có giá trị mặc định)
DATABASE_URL=sqlite+aiosqlite:///./chefgpt.db
REDIS_URL=redis://localhost:6379
LLM_PROVIDER=gemini                # gemini | openai | anthropic
ENVIRONMENT=development
```

## API Endpoints

### Auth
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/auth/signup` | Đăng ký |
| POST | `/auth/login` | Đăng nhập → access_token + refresh_token |
| POST | `/auth/refresh` | Làm mới token |
| POST | `/auth/logout` | Đăng xuất |

### Personas
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/personas` | Danh sách tất cả personas (system + custom) |
| GET | `/personas/{id}` | Chi tiết 1 persona |
| POST | `/personas` | Tạo custom persona mới |
| PUT | `/personas/{id}` | Cập nhật custom persona |
| DELETE | `/personas/{id}` | Xóa custom persona |
| GET | `/personas/me` | Persona đang active của user |
| PUT | `/personas/me` | Chọn persona + optional overrides |

### AI
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| POST | `/recipes/suggest` | Gợi ý món từ nguyên liệu + persona |
| POST | `/ingredients/recognize` | Nhận diện nguyên liệu từ ảnh |
| POST | `/mealplan/generate` | Tạo thực đơn + multi-persona |
| POST | `/chat/query` | Chat AI + persona + memory |
| GET | `/chat/history` | Lịch sử chat |

### Memory
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/memory/me` | Xem tất cả memory của user |
| POST | `/memory/me` | Thêm memory thủ công |
| DELETE | `/memory/me/{id}` | Xóa 1 memory |
| DELETE | `/memory/me` | Xóa toàn bộ memory |
| GET | `/memory/categories` | Danh sách 6 categories |

### Mock
| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/posts/mock` | 5 bài đăng mẫu |
| GET | `/shopping-list/mock` | Danh sách mua sắm mẫu |

## Project Structure

```
ChefGPT/
├── mobile/
│   └── lib/
│       ├── features/
│       │   ├── auth/              # Đăng nhập / đăng ký
│       │   ├── chat/              # AI chat + persona chip
│       │   ├── recipes/           # Gợi ý món + camera
│       │   ├── meal_plan/         # Lập thực đơn
│       │   ├── persona/           # Chọn & tạo AI persona
│       │   ├── memory/            # Quản lý user memory
│       │   ├── grocery/           # Mock shopping
│       │   ├── social/            # Mock social feed
│       │   └── profile/           # Hồ sơ người dùng
│       └── core/
│           ├── network/           # Dio API client
│           ├── router/            # GoRouter
│           └── theme/             # App colors & theme
├── backend/
│   └── app/
│       ├── routers/               # FastAPI endpoints
│       ├── services/
│       │   ├── llm/               # LLM abstraction (Gemini/OpenAI/Anthropic)
│       │   ├── persona_service.py # Load system persona JSONs
│       │   ├── persona_context.py # Resolve persona per-request
│       │   ├── memory_service.py  # User memory extraction & injection
│       │   ├── rag.py             # Semantic search (embeddings)
│       │   ├── cache.py           # Redis cache
│       │   └── key_manager.py     # API key rotation
│       ├── models/                # SQLModel DB models
│       ├── schemas/               # Pydantic schemas
│       ├── personas/              # 6 system persona JSON configs
│       ├── mocks/                 # Static mock data
│       └── alembic/               # DB migrations
└── README.md
```

## Testing

**Postman Collection**: `backend/ChefGPT.postman_collection.json`
1. Import vào Postman → **Import** → chọn file JSON
2. Chạy **Login** → token tự lưu vào `{{access_token}}`
3. Postman Settings → Request timeout → **180000 ms** (AI endpoints chậm)

**Swagger UI**: http://localhost:8000/docs

## AI Persona System

6 personas hệ thống có sẵn:

| ID | Tên | Đặc trưng |
|----|-----|-----------|
| `asian_chef` | Đầu bếp Á *(default)* | Việt/Nhật/Hàn/Thái, cân bằng 5 vị |
| `european_chef` | Đầu bếp Âu | Pháp/Ý/Địa Trung Hải, gợi ý rượu |
| `nutrition_expert` | Chuyên gia Dinh dưỡng | Macro chính xác, GI, TDEE |
| `vegan_chef` | Đầu bếp Chay | Thuần thực vật, thay thế sáng tạo |
| `home_chef` | Đầu bếp Gia đình | ≤30 phút, đơn giản, tiết kiệm |
| `fitness_coach` | Fitness Coach | Giàu protein, pre/post workout timing |

User và operator có thể tạo custom personas với full config (system prompt, recipe prefix, meal plan prefix, quick actions).

## User Memory System

AI tự động học facts về từng user qua hội thoại:

| Category | Mô tả | Ví dụ |
|----------|-------|-------|
| `dietary` | Chế độ ăn | dị ứng hải sản, ăn chay |
| `preference` | Sở thích | thích món Việt, thích cay |
| `aversion` | Không thích | ghét rau mùi |
| `goal` | Mục tiêu | giảm 5kg trong 3 tháng |
| `constraint` | Ràng buộc | chỉ có 30 phút nấu/bữa |
| `context` | Bối cảnh | tập gym 5 buổi/tuần |

Memory được inject vào system_prompt mỗi lần gọi AI. User có thể xem và xóa memory qua `/memory/me`.
