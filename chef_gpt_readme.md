# ChefGPT

ChefGPT is an AI-powered mobile application that helps users with cooking, meal planning, nutrition guidance, and grocery management. It integrates LLM-based reasoning, computer vision, and a social food-sharing community.

## Features

### 1. AI Recipe Generation
- Input ingredients via text or image.
- LLM analyzes available ingredients and suggests suitable dishes.
- Step-by-step cooking instructions.
- Optional video demonstrations.
- Filter by dietary preferences (non-spicy, non-oily, vegetarian, etc.).

### 2. Meal Planning & Nutrition
- Generate weekly meal plans.
- Eat Clean, Keto, weight-loss, muscle-gain recommendations.
- Automatic nutritional breakdown.

### 3. Grocery Assistance
- AI-generated shopping lists.
- "Smart market assistant" mode.

### 4. Social Cooking Community
- Share dishes, recipes, and cooking tips.
- Like, comment, and explore trending meals.

### 5. Future Expansion
- Integrations with supermarket APIs (Bách Hóa Xanh, Winmart, ShopeeFood, etc.).
- Automatic price comparison and online shopping.

## Tech Stack

### Mobile App
- Flutter / React Native
- State management: Provider, Riverpod or Redux

### Backend
- FastAPI (Python)
- PostgreSQL + pgvector
- Supabase (Auth, Storage, Realtime)
- Redis for caching

### AI / LLM
- GPT-4.1 + Vision
- Custom RAG pipeline using vector embeddings
- CV Model for ingredient recognition

### Infrastructure
- Docker + Kubernetes
- CI/CD using GitHub Actions
- Monitoring: Grafana + Prometheus

## Roadmap

### Phase 1: Core MVP
- Ingredient → Recipe generation
- Recipe instructions UI
- Basic meal plan generator
- User authentication

### Phase 2: Social & Grocery
- Social recipe sharing
- Shopping list auto-generation
- Nutrition engine

### Phase 3: AI Automation
- Personal diet assistant (agent-based)
- Supermarket API integrations
- Personalized health-based menus

## Development Guidelines
- Use modular architecture for mobile app
- Follow CLEAN Architecture for backend
- All AI processing goes through LLM Gateway layer

## License
Proprietary – for internal development and research.
