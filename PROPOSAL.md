# 🧑‍🍳 **ChefGPT – Mobile Cooking & Nutrition Assistant**

## **1. Mục tiêu & Giá trị cốt lõi**

ChefGPT là ứng dụng trợ lý ăn uống thông minh sử dụng LLM (GPT‑4.1) kết hợp Computer Vision nhằm:

* Giúp người dùng ăn uống khoa học, tiết kiệm, thuận tiện.
* Tự động hóa quá trình đưa ra thực đơn, đi chợ và nấu ăn.
* Cá nhân hoá chế độ ăn theo sức khỏe, sở thích, mục tiêu giảm cân/tăng cơ.
* Xây dựng cộng đồng chia sẻ công thức & kiến thức ăn uống.

---

## **2. Tổng quan sản phẩm**

ChefGPT là mobile app dạng chatbot AI với nhiều tính năng tập trung vào việc gợi ý món ăn, lập thực đơn, phân tích dinh dưỡng và hỗ trợ nấu ăn từ nguyên liệu có sẵn. Ứng dụng hướng đến người Việt, tối ưu theo văn hoá ẩm thực Việt Nam.

---

## **3. Các nhóm tính năng chính**

### **A. Chatbot Agent – Trung tâm ứng dụng**

Giao diện hội thoại chính, tích hợp các quick actions và AI reasoning.

#### **1. Đề xuất món ăn / Công thức (Recipe Recommendation Engine)**

* Nhập nguyên liệu bằng text, ảnh chụp hoặc ảnh thư viện.
* Vision Model nhận diện loại nguyên liệu, độ tươi, số lượng tương đối.
* Nhập tên món trực tiếp để xem công thức.
* Nhập yêu cầu theo khẩu vị: món nước, không cay, healthy, ít béo, 15 phút…
* LLM phân tích → gợi ý danh sách món phù hợp.

**Hướng dẫn chi tiết mỗi món gồm:**

* Nguyên liệu (phân chia: có sẵn – cần mua)
* Thời gian nấu, độ khó
* Hàm lượng calories & dinh dưỡng
* Các bước nấu kèm minh họa
* Video hướng dẫn (YouTube hoặc từ cộng đồng)
* Tùy biến món: phiên bản healthy, rẻ hơn, ăn kiêng, thay thế nguyên liệu

#### **2. Lập thực đơn tự động**

Người dùng nhập mục tiêu:

* Giảm cân, tăng cơ, eat clean
* Dinh dưỡng theo nhu cầu (high protein, low carb…)

Agent tạo:

* Menu ngày/tuần
* Calories & macro cho từng bữa
* Danh sách nguyên liệu cần mua (auto‑shopping list)

#### **3. Đi chợ thông minh**

* Người dùng gửi ảnh tủ lạnh → CV nhận diện nguyên liệu còn lại.
* Gợi ý món phù hợp + nguyên liệu thiếu.
* Tự động sinh giỏ hàng.

**Tương lai**:

* Kết nối Bách Hóa Xanh, Winmart, ShopeeFood → cho phép đặt hàng trực tiếp.

#### **4. Tư vấn dinh dưỡng & thói quen ăn uống**

Ví dụ:

* “Tôi có nên bỏ bữa sáng không?”
* “Trứng ăn với cà chua có tốt không?”
* “Tôi đau dạ dày thì nên ăn gì?”

Agent trả lời dưới tone chuyên gia sức khỏe – an toàn – đáng tin cậy.

---

### **B. Social Features – Share Space**

Không gian cộng đồng để:

* Đăng bài, video, công thức nấu ăn.
* Like, comment, bookmark.
* Gợi ý bài viết theo khẩu vị (ML‑based).

**Đặc biệt**: mỗi công thức từ cộng đồng có thể “convert” bằng AI:

* Nấu phiên bản healthy
* Nấu theo nguyên liệu người dùng có
* Rút gọn thời gian

---

### **C. Health / Personalization Layer**

* Hồ sơ dinh dưỡng: tuổi, cân nặng, chiều cao, khẩu vị.
* Dị ứng, bệnh nền (tuỳ chọn – không bắt buộc).
* Theo dõi calories từng bữa.
* Nhắc uống nước, nhắc giờ ăn.
* Tích hợp Apple Health / Google Fit.

---

## **4. User Flow – Luồng người dùng**

### **1. Onboarding**

* Đăng nhập (email / Google / Apple).
* Survey mục tiêu ăn uống.
* Hướng dẫn sử dụng chatbot.

### **2. Màn hình chính**

Chatbot + Quick Actions:

* 📷 Chụp nguyên liệu
* 🍽 Gợi ý món
* 🛒 Danh sách đi chợ
* 🍱 Lên thực đơn tuần
* ❤️ Eat Clean Guide

### **3. Social Feed**

* Xem bài từ cộng đồng.
* Lọc theo loại món, độ khó, chế độ ăn.

### **4. Shopping List**

* Tự động sinh từ công thức / meal plan.
* Gợi ý combo nguyên liệu tiết kiệm.

### **5. Hồ sơ cá nhân**

* Lịch sử món đã nấu, thực đơn, thống kê dinh dưỡng.

---

## **5. Tech Stack & Kiến trúc**

### **Mobile App**

**Option 1 – Flutter (khuyên dùng)**

* UI đẹp, hiệu năng cao.
* State management: Riverpod / Bloc.

**Option 2 – React Native**

* Cộng đồng lớn, dễ mở rộng.

### **Backend**

* FastAPI (Python) – API nhanh, dễ mở rộng.
* Node.js – xử lý realtime nếu cần.

### **LLM Layer**

* GPT‑4.1 (core reasoning)
* GPT‑4.1 Vision / Gemini 2.0 Vision

### **RAG Layer**

* PostgreSQL + pgvector
* Index: công thức món Việt, dinh dưỡng, mẹo nấu ăn

### **Database**

* PostgreSQL
* Supabase Storage or Firebase Storage
* Redis cache

### **Infrastructure**

* Supabase (auth + storage + realtime)
* Deploy backend: Fly.io / Azure / AWS / Vercel

### **Computer Vision**

* Model: GPT‑4.1 Vision hoặc YOLOv8 custom

---

## **6. Business Model**

### **1. Freemium (gợi ý chính)**

**Miễn phí:**

* Chat cơ bản
* 10 đề xuất món/ngày
* Social Feed
* Calories tracking cơ bản

**Premium (79k – 119k/tháng):**

* GPT‑4.1 không giới hạn
* Lập thực đơn thông minh
* Đi chợ AI nâng cao
* Phân tích ảnh nguyên liệu không giới hạn
* Gợi ý món theo chi phí
* Phân tích dinh dưỡng chuyên sâu

### **2. Affiliate / Partnership**

* Bách Hóa Xanh, Winmart
* ShopeeFood / GrabFood
* Đồ gia dụng & thiết bị bếp

### **3. Native Ads**

* Gợi ý mua nguyên liệu
* Promo siêu thị gần bạn

### **4. Bán nội dung trả phí**

* Gói Eat Clean 30 ngày
* Gói giảm cân
* Gói meal prep cho gymer

---

## **7. Lộ trình phát triển (Roadmap)**

### **Phase 1 – MVP (2 tháng)**

* Chatbot
* Đề xuất món từ nguyên liệu
* Nhận diện nguyên liệu từ ảnh
* Recipe detail
* Shopping list
* User account

### **Phase 2 – Growth (3–6 tháng)**

* Social Feed
* Eat Clean Mode
* Meal Plan tuần
* Calories tracking
* Gợi ý món tiết kiệm chi phí

### **Phase 3 – Monetization**

* Gói Premium
* Content Packs
* Hợp tác siêu thị

### **Phase 4 – Expansion**

* Đi chợ online toàn diện
* AI video generator
* Voice assistant
* Mở rộng sang thị trường Đông Nam Á

---

## **8. Cải tiến đề xuất thêm**

* Gợi ý món theo mood (buồn, bận rộn, mệt mỏi…)
* Scan bill siêu thị → cập nhật tủ lạnh tự động
* Nấu theo video YouTube
* Phân tích thói quen ăn uống tuần/tháng
* Budget mode: đề xuất món theo ngân sách

---

## **9. Kết luận**

ChefGPT có tiềm năng trở thành ứng dụng ăn uống & dinh dưỡng thông minh hàng đầu tại Việt Nam nhờ khả năng kết hợp LLM + Vision + RAG + Social Community, tạo ra trải nghiệm toàn diện cho người dùng từ việc nấu ăn, đi chợ đến tối ưu sức khỏe.

## 6. Mobile App Design (Tech Stack, Architecture, UI/UX, Backend, Roadmap, Pitch Deck)

### 6.1 Tech Stack Overview

**Frontend (Mobile App):**

* React Native (Expo) hoặc Flutter
* State management: Redux Toolkit / Zustand (RN), hoặc Riverpod/Bloc (Flutter)
* UI Library: NativeWind (RN) hoặc Flutter Material 3
* Realtime: WebSocket hoặc Firebase Realtime Database
* Image processing: native Vision API bridging

**Backend:**

* Node.js (NestJS) hoặc Python FastAPI
* PostgreSQL + Prisma ORM
* Redis caching
* Firebase Authentication / Auth0
* S3/Cloudflare R2 để lưu ảnh món
* Supabase hoặc Hasura (tuỳ chọn) cho realtime event

**AI Layer:**

* OpenAI GPT‑4.1 cho core reasoning
* GPT‑4.1 Vision cho xử lý ảnh
* Finetuned local embeddings (PGVector) để RAG công thức nấu ăn
* Moderation API

**Infrastructure:**

* Docker + Kubernetes (GKE/AWS)
* API Gateway + Load Balancer
* CI/CD: GitHub Actions
* Analytics: Mixpanel, Firebase Analytics

---

### 6.2 System Architecture

**Client → API Gateway → Backend Services:**

1. **Recipe Service:** CRUD công thức, scoring món ăn
2. **User Profile Service:** khẩu vị, dị ứng, lịch sử nấu
3. **Vision Processing Service:** nhận dạng nguyên liệu → vector embedding
4. **Recommendation Engine:** LLM + RAG + rule-based filters
5. **Marketplace Service:** kết nối siêu thị/đi chợ online (tương lai)
6. **Notification Service:** gợi ý món theo giờ, push reminders

**Data Flow ví dụ:**

* Upload ảnh tủ lạnh → Vision → detect ingredients → gửi danh sách → LLM generate đề xuất món → trả UI.

---

### 6.3 UI/UX Design

**Core Principles:**

* 3-tab layout: Chat – Recipes – Share Space
* Luồng tối ưu 2‑step: Chụp ảnh → ChefGPT trả gợi ý ngay
* Color palette: nấu ăn, tự nhiên → xanh lá + trắng + accent vàng
* Component chính: Chat widget, Recipe card, Step-by-step cooking mode

**Screens:**

1. **Onboarding:** chọn chế độ ăn, dị ứng, sở thích
2. **Home/Chat:** chatbot + quick actions (Scan tủ lạnh / Gợi ý nhanh / Eat Clean / Low Budget)
3. **Recipe Detail:** nguyên liệu, calories, video, step
4. **Cooking Mode:** dạng TikTok steps, đọc giọng nói, hẹn giờ
5. **Share Space:** bài đăng, like/comment, upload recipe
6. **Profile:** chỉ số calories, history, settings

---

### 6.4 Backend Detailed Modules

1. **LLM Controller** – gọi GPT 4.1, tối ưu token, chain-of-thought nội bộ
2. **Ingredient Recognition** – Vision API + confidence threshold
3. **Recipe Generator** – Hoán đổi nguyên liệu, biến tấu, scaling khẩu phần
4. **Nutrition Calculator** – tính calories theo USDA database
5. **User Personalization Engine** – học hành vi → gợi ý theo thói quen
6. **Search + RAG** – semantic search công thức theo vector embedding

---

### 6.5 Roadmap (6 tháng)

**Tháng 1:**

* App skeleton + Firebase Auth + Chat UI
* Basic GPT‑4.1 chat + đề xuất món theo text

**Tháng 2:**

* Vision: nhận dạng nguyên liệu từ ảnh
* Recipe detail + cooking mode

**Tháng 3:**

* Share Space (bản cơ bản)
* RAG database cho công thức VN

**Tháng 4:**

* Tối ưu backend, caching, analytics
* Chế độ ăn kiêng: Eat Clean, Keto, High Protein

**Tháng 5:**

* Tính calories tự động + Meal plan 7 ngày
* Marketplace API chuẩn bị kết nối siêu thị

**Tháng 6:**

* Release bản Beta + chiến dịch marketing
* Thu thập feedback → refine UX

---

### 6.6 Business Model

**Freemium + Subscription + Marketplace Revenue**

**1. Freemium (miễn phí):**

* Chat cơ bản
* 5 gợi ý món/ngày
* Share Space

**2. Pro Subscription (~59k–99k/tháng):**

* Unlimited chat + Vision
* Meal plan 7–30 ngày
* Phân tích dinh dưỡng chi tiết
* Video tutorials premium
* Cloud cookbook

**3. In-app purchases:**

* Gói công thức đặc biệt: healthy, gym, người giảm cân
* Hướng dẫn nấu ăn theo chủ đề

**4. Marketplace Affiliate:**

* Gợi ý nguyên liệu còn thiếu → mua ở Bách Hoá Xanh / Winmart
* Mỗi đơn hàng nhận 3–10% affiliate

**5. Corporate/Partner:**

* Hợp tác KOL food, đầu bếp → bán khóa học nấu ăn mini

---

### 6.7 Business Pitch Deck Structure

1. **Problem:** Người Việt ăn uống thiếu kế hoạch, phí nguyên liệu, không biết nấu gì hôm nay.
2. **Solution:** ChefGPT – AI Cooking Assistant với Vision + LLM.
3. **Product Demo:** scan tủ lạnh → gợi ý món → cooking mode.
4. **Market:** 100M dân Việt, 40M người trẻ dùng smartphone.
5. **Business Model:** Freemium + Subscription + Marketplace.
6. **Competitive Landscape:** Cookpad, Instagram Recipes, Google – nhưng không có AI real-time + personalization.
7. **Traction:** dự kiến 50k user Month 1.
8. **Tech Advantage:** LLM + Vision + RAG VN cuisine.
9. **Roadmap:** 6 tháng ra mắt phiên bản thương mại.
10. **Ask:** gọi vốn 100k–300k USD để scale.

---

Nếu bạn muốn, tôi có thể tiếp tục tạo **UI wireframe**, **Sơ đồ kiến trúc dạng hình**, hoặc **Pitch Deck dạng slide PDF**.
