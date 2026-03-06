# ChefGPT Backend API

FastAPI backend cho **ChefGPT MVP** — trợ lý nấu ăn và dinh dưỡng AI.

- **AI**: Gemini 2.5 Flash (Google AI Studio — free tier)
- **Database**: SQLite (local dev) — không cần cài PostgreSQL
- **Auth**: JWT tự quản lý (python-jose + passlib)

---

## Tính năng MVP

| Tính năng | Endpoint | AI |
|-----------|----------|----|
| Gợi ý món ăn từ nguyên liệu | `POST /recipes/suggest` | Gemini 2.5 Flash |
| Nhận dạng nguyên liệu từ ảnh | `POST /ingredients/recognize` | Gemini Vision |
| Chat hỏi đáp nấu ăn | `POST /chat/query` | Gemini 2.5 Flash |
| Tạo thực đơn theo tuần | `POST /mealplan/generate` | Gemini 2.5 Flash |
| Feed cộng đồng | `GET /posts/mock` | Mock JSON |
| Danh sách mua sắm | `GET /shopping-list/mock` | Mock JSON |

---

## Tech Stack

| Layer | Công nghệ |
|-------|-----------|
| Framework | FastAPI 0.109+ |
| Database | SQLite + aiosqlite (async) |
| ORM | SQLModel (SQLAlchemy 2.0) |
| Auth | JWT — python-jose + passlib[bcrypt==3.2.2] |
| AI | google-genai (Gemini 2.5 Flash) |
| Python | 3.11+ (conda env: `ChefGPT`) |

---

## Cấu trúc thư mục

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py        # Settings từ .env
│   │   ├── database.py      # SQLite async engine
│   │   └── security.py      # JWT helpers
│   ├── models/              # SQLModel DB models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API endpoints
│   │   ├── auth.py          # /auth/*
│   │   ├── recipes.py       # /recipes/*
│   │   ├── vision.py        # /ingredients/recognize
│   │   ├── chat.py          # /chat/*
│   │   ├── meal_plan.py     # /mealplan/*
│   │   ├── social.py        # /posts/mock
│   │   └── shopping.py      # /shopping-list/mock
│   ├── services/
│   │   └── gemini.py        # GeminiService — điểm AI duy nhất
│   ├── mocks/               # Dữ liệu tĩnh
│   │   ├── posts.json
│   │   └── shopping.json
│   └── main.py
├── .env                     # Secrets (không commit)
├── .env.example
├── requirements.txt
├── curl_examples.sh         # cURL examples tất cả endpoint
└── ChefGPT.postman_collection.json
```

---

## Cài đặt và chạy

### Yêu cầu

- [Anaconda](https://www.anaconda.com/) hoặc Python 3.11+
- Gemini API Key — lấy miễn phí tại [aistudio.google.com](https://aistudio.google.com/)

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

> **Lưu ý**: `passlib==1.7.4` yêu cầu `bcrypt==3.2.2`. Nếu dùng bcrypt 4.x sẽ lỗi.

### Bước 3 — Cấu hình môi trường

```bash
cp .env.example .env
```

Các biến bắt buộc trong `.env`:

```env
GEMINI_API_KEY=AIza...          # Lấy từ Google AI Studio
JWT_SECRET_KEY=your-secret-key  # Chuỗi ngẫu nhiên bất kỳ
```

> SQLite DB (`chefgpt.db`) tự động tạo khi khởi động — không cần cài thêm gì.

### Bước 4 — Khởi động server

```bash
# Windows (conda env ChefGPT)
/d/Anaconda/envs/ChefGPT/python.exe -m uvicorn app.main:app --reload

# Mac/Linux (sau conda activate ChefGPT)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server chạy tại: `http://localhost:8000`

---

## API Endpoints

### Health

```
GET /health
```

Không cần auth. Kiểm tra server đang chạy.

---

### Auth

```
POST /auth/signup     Đăng ký tài khoản mới
POST /auth/login      Đăng nhập, nhận access_token + refresh_token
POST /auth/refresh    Làm mới access_token (dùng refresh_token)
POST /auth/logout     Đăng xuất
```

Response mẫu (login/signup):

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "user@example.com", "name": "Nguyen Van A" }
}
```

> `access_token` hết hạn sau **1 giờ**. `refresh_token` hết hạn sau **7 ngày**.

---

### AI — Gợi ý món ăn *(~30–120 giây)*

```
POST /recipes/suggest
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
// Request
{ "ingredients": ["trứng", "cà chua", "hành lá"], "filters": ["ít dầu"] }

// Response
{
  "dishes": [{
    "name": "Trứng chiên cà chua",
    "description": "Món đơn giản, đậm đà",
    "steps": ["Bước 1...", "Bước 2..."],
    "time_minutes": 15,
    "difficulty": "easy",
    "nutrition": { "calories": 250, "protein": 12, "carbs": 8, "fat": 18 }
  }]
}
```

---

### AI — Nhận dạng nguyên liệu từ ảnh *(Gemini Vision)*

```
POST /ingredients/recognize
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
Form field: image (file JPG/PNG)
```

```json
{ "ingredients": ["cà chua", "trứng", "hành tây"] }
```

---

### AI — Chat hỏi đáp nấu ăn *(~3–10 giây)*

```
POST /chat/query
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
// Request
{ "message": "Gợi ý bữa sáng cho người ăn kiếng", "session_id": null }

// Response
{ "id": "5", "message": "Bạn có thể thử yến mạch...", "role": "assistant", "timestamp": "..." }
```

> Truyền `session_id` từ response trước để tiếp tục hội thoại.

```
GET /chat/history     Lịch sử chat (phân theo session)
```

---

### AI — Tạo thực đơn *(~60–120 giây)*

```
POST /mealplan/generate
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
// Request
{ "goal": "eat_clean", "days": 3, "calories_target": 1800 }
```

| `goal` | Ý nghĩa |
|--------|---------|
| `eat_clean` | Ăn sạch, lành mạnh |
| `weight_loss` | Giảm cân |
| `muscle_gain` | Tăng cơ |
| `keto` | Keto (ít carb) |
| `maintenance` | Duy trì cân nặng |

```json
// Response
{
  "id": 1, "goal": "eat_clean", "days": 3, "calories_target": 1800,
  "plan": [{ "day": 1, "meals": { "breakfast": "Yến mạch sữa... (350 kcal)", "lunch": "...", "dinner": "..." } }],
  "nutrition_summary": { "avg_calories": 1800, "avg_protein": 110, "avg_carbs": 180, "avg_fat": 55, "notes": "..." }
}
```

```
GET /mealplan     Danh sách thực đơn đã lưu của user
```

---

### Mock — Social & Grocery *(không cần auth)*

```
GET /posts/mock          5 bài đăng mẫu từ cộng đồng
GET /shopping-list/mock  Danh sách mua sắm (4 nhóm: Rau củ, Thịt, Ngũ cốc, Gia vị)
```

---

## Biến môi trường

Xem đầy đủ trong `.env.example`. Các biến bắt buộc:

```env
GEMINI_API_KEY=AIza...
JWT_SECRET_KEY=your-random-secret-32-chars
DATABASE_URL=sqlite+aiosqlite:///./chefgpt.db
CORS_ORIGINS=http://localhost:3000,http://localhost:5000,http://localhost:8000
ENVIRONMENT=development
DEBUG=true
```

---

## Tài liệu API

| URL | Mô tả |
|-----|-------|
| http://localhost:8000/docs | Swagger UI — thử trực tiếp trên browser |
| http://localhost:8000/redoc | ReDoc — tài liệu đẹp hơn |

---

## Testing với cURL và Postman

**cURL examples** (tất cả endpoint):
```bash
bash curl_examples.sh
```

**Postman Collection:**
1. Mở Postman → **Import** → chọn `ChefGPT.postman_collection.json`
2. Chạy **Login** → token tự động lưu vào `{{access_token}}`
3. Test tất cả endpoint trực tiếp

> **Lưu ý Postman**: AI endpoints cần 60–120 giây → *Settings → Request timeout* đặt **180000 ms**.

---

## Lưu ý khi phát triển

- **AI response chậm**: Gemini 2.5 Flash thinking mode — bình thường mất 30–120 giây cho recipe/mealplan. Chat nhanh hơn (~5 giây).
- **Mọi AI call** đi qua `GeminiService` tại `app/services/gemini.py` — không gọi Gemini trực tiếp ở router.
- **Mock data** tại `app/mocks/posts.json` và `app/mocks/shopping.json`.

---

## Roadmap

- **Phase 1 — MVP** ✅ (hiện tại): AI recipe + meal plan + chat + mock social/grocery
- **Phase 2 — Social thật**: Supabase Realtime, user posts, likes, comments
- **Phase 3 — Grocery thật**: Shopping list sinh từ thực đơn, API siêu thị
- **Phase 4 — Scale**: PostgreSQL, Redis cache, deploy Railway/Render
