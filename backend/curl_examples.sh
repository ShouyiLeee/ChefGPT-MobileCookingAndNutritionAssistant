#!/bin/bash
# ChefGPT Backend — cURL Examples
# Base URL: http://localhost:8000
# Docs:     http://localhost:8000/docs  (Swagger UI)
#
# Usage:
#   Chạy từng lệnh độc lập, hoặc chạy cả file:
#     chmod +x curl_examples.sh && ./curl_examples.sh
#
# Note: Thay TOKEN bằng access_token lấy từ bước Login bên dưới.

BASE="http://localhost:8000"
TOKEN="<paste_access_token_here>"

echo "========================================"
echo " ChefGPT API — cURL Examples"
echo "========================================"

# ─────────────────────────────────────────────
# 1. HEALTH CHECK
# ─────────────────────────────────────────────

echo -e "\n[1] Health Check"
curl -s "$BASE/health" | python3 -m json.tool

# Expected:
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "development"
# }


# ─────────────────────────────────────────────
# 2. AUTH — ĐĂNG KÝ
# ─────────────────────────────────────────────

echo -e "\n[2] Đăng ký tài khoản"
curl -s -X POST "$BASE/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!",
    "name": "Nguyen Van A"
  }' | python3 -m json.tool

# Expected:
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "user": { "id": "uuid", "email": "user@example.com", "name": "Nguyen Van A" }
# }


# ─────────────────────────────────────────────
# 3. AUTH — ĐĂNG NHẬP
# ─────────────────────────────────────────────

echo -e "\n[3] Đăng nhập"
curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!"
  }' | python3 -m json.tool

# → Copy access_token từ response vào biến TOKEN bên dưới


# ─────────────────────────────────────────────
# 4. AUTH — REFRESH TOKEN
# ─────────────────────────────────────────────

echo -e "\n[4] Refresh token"
curl -s -X POST "$BASE/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<paste_refresh_token_here>"
  }' | python3 -m json.tool


# ─────────────────────────────────────────────
# 5. AUTH — ĐĂNG XUẤT
# ─────────────────────────────────────────────

echo -e "\n[5] Đăng xuất"
curl -s -X POST "$BASE/auth/logout" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# ─────────────────────────────────────────────
# 6. MOCK — SOCIAL FEED (không cần auth)
# ─────────────────────────────────────────────

echo -e "\n[6] Mock social feed"
curl -s "$BASE/posts/mock" | python3 -m json.tool

# Expected:
# {
#   "posts": [
#     { "id": 1, "author": { "name": "Nguyễn Thị Lan", ... }, "content": "...", ... },
#     ...
#   ]
# }


# ─────────────────────────────────────────────
# 7. MOCK — DANH SÁCH MUA SẮM (không cần auth)
# ─────────────────────────────────────────────

echo -e "\n[7] Mock shopping list"
curl -s "$BASE/shopping-list/mock" | python3 -m json.tool

# Expected:
# {
#   "categories": [
#     { "name": "Rau củ", "items": [ { "name": "Cà chua", ... } ] },
#     ...
#   ]
# }


# ─────────────────────────────────────────────
# 8. AI — GỢI Ý MÓN ĂN (Gemini 2.5 Flash, ~30-120s)
# ─────────────────────────────────────────────

echo -e "\n[8] Gợi ý món ăn từ nguyên liệu (AI — có thể mất 30-120s)"
curl -s -X POST "$BASE/recipes/suggest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ingredients": ["trứng", "cà chua", "hành lá"],
    "filters": ["ít dầu", "nhanh"]
  }' | python3 -m json.tool

# Expected:
# {
#   "dishes": [
#     {
#       "name": "Trứng chiên cà chua",
#       "description": "...",
#       "steps": ["bước 1", "bước 2", "..."],
#       "time_minutes": 15,
#       "difficulty": "easy",
#       "nutrition": { "calories": 250, "protein": 12, "carbs": 8, "fat": 18 }
#     },
#     ...
#   ]
# }


# ─────────────────────────────────────────────
# 9. AI — CHAT VỚI CHEFGPT (Gemini, ~3-10s)
# ─────────────────────────────────────────────

echo -e "\n[9] Chat với ChefGPT AI"
curl -s -X POST "$BASE/chat/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Gợi ý món ăn sáng đơn giản cho người bận rộn",
    "session_id": null
  }' | python3 -m json.tool

# Expected:
# {
#   "id": "5",
#   "message": "Cho bữa sáng nhanh gọn, bạn có thể thử...",
#   "role": "assistant",
#   "timestamp": "2026-03-05T..."
# }

# Chat với lịch sử:
# curl -s -X POST "$BASE/chat/query" \
#   -H "Authorization: Bearer $TOKEN" \
#   -H "Content-Type: application/json" \
#   -d '{"message": "Cách làm cụ thể?", "session_id": 5}'


# ─────────────────────────────────────────────
# 10. AI — TẠO THỰC ĐƠN (Gemini, ~60-120s)
# ─────────────────────────────────────────────

echo -e "\n[10] Tạo thực đơn AI (mất 60-120s)"
curl -s -X POST "$BASE/mealplan/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --max-time 180 \
  -d '{
    "goal": "eat_clean",
    "days": 3,
    "calories_target": 1800
  }' | python3 -m json.tool

# goal options: "eat_clean" | "weight_loss" | "muscle_gain" | "keto" | "maintenance"
# days: 1–14
# calories_target: 1000–5000

# Expected:
# {
#   "id": 1,
#   "goal": "eat_clean",
#   "days": 3,
#   "calories_target": 1800,
#   "plan": [
#     { "day": 1, "meals": { "breakfast": "Yến mạch sữa...", "lunch": "Cơm gạo lứt...", "dinner": "Ức gà hấp..." } }
#   ],
#   "nutrition_summary": { "avg_calories": 1800, "avg_protein": 100, ... }
# }


# ─────────────────────────────────────────────
# 11. LỊCH SỬ THỰC ĐƠN ĐÃ LƯU
# ─────────────────────────────────────────────

echo -e "\n[11] Danh sách thực đơn đã lưu"
curl -s "$BASE/mealplan" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# ─────────────────────────────────────────────
# 12. LỊCH SỬ CHAT
# ─────────────────────────────────────────────

echo -e "\n[12] Lịch sử chat"
curl -s "$BASE/chat/history" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool


# ─────────────────────────────────────────────
# 13. AI — NHẬN DẠNG NGUYÊN LIỆU TỪ ẢNH (Gemini Vision)
# ─────────────────────────────────────────────

echo -e "\n[13] Nhận dạng nguyên liệu từ ảnh"
# Thay food.jpg bằng ảnh thực tế
curl -s -X POST "$BASE/ingredients/recognize" \
  -H "Authorization: Bearer $TOKEN" \
  -F "image=@/path/to/food.jpg" | python3 -m json.tool

# Expected:
# {
#   "ingredients": ["cà chua", "trứng", "hành tây"]
# }


echo -e "\n========================================"
echo " Xem Swagger UI tại: http://localhost:8000/docs"
echo "========================================"
