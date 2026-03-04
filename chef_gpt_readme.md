# ChefGPT – MVP

ChefGPT là ứng dụng mobile AI giúp người dùng nấu ăn thông minh hơn: gợi ý món từ nguyên liệu có sẵn, lên kế hoạch bữa ăn, và theo dõi dinh dưỡng. MVP tập trung vào core AI workflow, các tính năng phụ sử dụng mock data.

---

## Core AI Workflow (Thực thi thật)

### 1. AI Recipe Generation
- Người dùng nhập nguyên liệu bằng text hoặc chụp ảnh.
- Gemini 2.5 Flash phân tích và gợi ý món ăn phù hợp.
- Trả về hướng dẫn nấu từng bước.
- Lọc theo sở thích: không cay, chay, ít dầu, v.v.

### 2. Meal Planning & Nutrition
- Tạo kế hoạch bữa ăn theo tuần dựa trên mục tiêu (giảm cân, tăng cơ, eat clean...).
- Gemini 2.5 Flash sinh thực đơn và phân tích dinh dưỡng tự động.

---

## Mock Features (Demo MVP)

### 3. Grocery Assistance *(mock)*
- Danh sách mua sắm được sinh sẵn tĩnh từ công thức.
- Không tích hợp API siêu thị ở giai đoạn này.

### 4. Social Cooking Community *(mock)*
- Hiển thị feed bài đăng, like, comment từ dữ liệu mẫu cứng.
- Không có backend realtime, không có user-generated content thật.

---

## Tech Stack (Simplified MVP)

### Mobile App
- **Flutter** (đơn giản, cross-platform, 1 codebase)
- State management: **Riverpod**

### Backend
- **FastAPI** (Python) – nhẹ, nhanh, dễ deploy
- **SQLite** (local dev) → PostgreSQL (khi scale)
- **Supabase Auth** – xác thực người dùng

### AI / LLM
- **Gemini 2.5 Flash** via Google AI Studio API (free tier)
- Prompt engineering trực tiếp – không cần RAG hay vector DB ở MVP
- Nhận diện ảnh nguyên liệu: dùng Gemini Vision (multimodal, không cần CV model riêng)

### Infrastructure
- **Docker Compose** (local dev)
- Deploy: **Railway / Render** (free tier)
- Không cần Kubernetes ở giai đoạn MVP

---

## Architecture (MVP)

```
Mobile (Flutter)
    │
    ▼
FastAPI Backend
    ├── /recipe      → Gemini 2.5 Flash (text + vision)
    ├── /meal-plan   → Gemini 2.5 Flash
    ├── /grocery     → Mock response
    └── /social      → Mock response
    │
    ▼
Supabase (Auth + SQLite/Postgres lưu history)
```

---

## Roadmap

### Phase 1 – MVP (hiện tại)
- [x] Nhập nguyên liệu → gợi ý món (Gemini 2.5 Flash)
- [x] Chụp ảnh nguyên liệu → nhận diện bằng Gemini Vision
- [x] Tạo thực đơn tuần + phân tích dinh dưỡng
- [x] Xác thực người dùng (Supabase Auth)
- [x] Social feed & grocery list (mock data)

### Phase 2 – Social & Grocery
- Social recipe sharing thật (Supabase Realtime)
- Danh sách mua sắm tự sinh từ thực đơn

### Phase 3 – AI Automation
- Tích hợp API siêu thị (Bách Hóa Xanh, Winmart, ShopeeFood)
- Agent cá nhân hoá chế độ ăn theo sức khỏe
- Nâng cấp model nếu cần (Gemini Pro / Claude)

---

## Development Guidelines
- Mỗi AI call đi qua một service layer duy nhất (`GeminiService`) để dễ swap model sau này.
- Mock data đặt trong thư mục `/mocks`, tách biệt với business logic.
- Không hardcode API key – dùng `.env`.

## License
Proprietary – internal development and research.
