# ChefGPT — AI Cooking & Nutrition Assistant

Mobile app trợ lý nấu ăn và dinh dưỡng AI, powered by **Gemini 2.5 Flash**.

## Features

| Feature | Status | Description |
|---------|--------|-------------|
| AI Recipe Suggestion | Real | Nhập nguyên liệu (text hoặc ảnh) → Gemini gợi ý 3 món |
| Ingredient Recognition | Real | Chụp ảnh nguyên liệu → Gemini Vision nhận diện tự động |
| Meal Plan Generator | Real | Tạo thực đơn tuần theo mục tiêu (giảm cân, tăng cơ, eat clean...) |
| Nutrition Chat | Real | Chat với AI về dinh dưỡng và công thức nấu ăn |
| Grocery Shopping | Mock | Chọn cửa hàng (BHX, WinMart, CoopMart...), giỏ hàng, thanh toán |
| Social Feed | Mock | Feed bài đăng công thức, like, comment |

## Tech Stack

**Mobile**: Flutter + Riverpod + Dio + GoRouter

**Backend**: FastAPI + SQLite + Supabase Auth

**AI**: Gemini 2.5 Flash (text + vision, free tier via Google AI Studio)

## Architecture

```
Flutter App
    │
    ▼
FastAPI Backend (Python)
    ├── POST /recipes/suggest       → GeminiService
    ├── POST /ingredients/recognize → GeminiService (vision)
    ├── POST /mealplan/generate     → GeminiService
    ├── POST /chat/query            → GeminiService
    ├── GET  /posts                 → SQLite (social feed)
    └── GET  /shopping-list/mock    → Mock JSON
    │
    ▼
SQLite (local) / PostgreSQL (production)
Supabase Auth (JWT)
```

## Quick Start

### Backend

```bash
# 1. Tạo môi trường và cài thư viện
conda create -n ChefGPT python=3.11
conda activate ChefGPT
pip install -r backend/requirements.txt

# 2. Cấu hình .env
cp backend/.env.example backend/.env
# Điền GEMINI_API_KEY vào backend/.env
# Lấy API key miễn phí tại: https://aistudio.google.com

# 3. Chạy server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

### Mobile

```bash
cd mobile
flutter pub get
flutter run  # Chrome/emulator

# Build APK cho Android thật
flutter build apk --debug
```

**Lưu ý**: Đổi `baseUrl` trong `mobile/lib/core/constants/app_constants.dart` theo môi trường:
- Android emulator: `http://10.0.2.2:8000`
- Android thật (cùng WiFi): `http://<IP_PC>:8000`
- Production: URL của Railway/Render

## Environment Variables

Tạo file `backend/.env` từ `backend/.env.example`:

```env
GEMINI_API_KEY=your_key_here       # https://aistudio.google.com
DATABASE_URL=sqlite:///./chefgpt.db
JWT_SECRET_KEY=your_secret_here
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
```

**Không commit file `.env`** — đã gitignore.

## Project Structure

```
ChefGPT/
├── mobile/                        # Flutter app
│   ├── lib/
│   │   ├── features/
│   │   │   ├── chat/              # AI chat
│   │   │   ├── recipes/           # Recipe suggestion + camera
│   │   │   ├── meal_plan/         # Meal planner
│   │   │   ├── grocery/           # Mock shopping
│   │   │   └── social/            # Mock social feed
│   │   ├── core/
│   │   │   ├── network/           # Dio API client
│   │   │   ├── router/            # GoRouter
│   │   │   └── constants/
│   │   └── main.dart
│   └── android/                   # Android platform
├── backend/
│   ├── app/
│   │   ├── routers/               # FastAPI endpoints
│   │   ├── services/
│   │   │   └── gemini.py          # GeminiService (single AI entry point)
│   │   ├── models/                # SQLAlchemy models
│   │   ├── schemas/               # Pydantic schemas
│   │   └── mocks/                 # Mock JSON data
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Đăng ký |
| POST | `/auth/login` | Đăng nhập |
| POST | `/recipes/suggest` | Gợi ý món từ nguyên liệu |
| POST | `/ingredients/recognize` | Nhận diện nguyên liệu từ ảnh |
| POST | `/mealplan/generate` | Tạo thực đơn |
| POST | `/chat/query` | Chat AI |
| GET | `/posts` | Social feed |
| GET | `/shopping-list/mock` | Mock grocery list |
