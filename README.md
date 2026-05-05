# AI Teaching Platform

Платформа для учителей с ИИ-ассистентом. 5 типов заданий, адаптивная сложность, live сессии через QR.

## Быстрый старт

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
# Добавьте CLAUDE_API_KEY в .env
uvicorn app.main:app --reload
```
Документация: http://localhost:8000/docs

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
Сайт: http://localhost:5173

### 3. Docker (с базой данных)
```bash
docker-compose -f docker-compose.dev.yml up
```

## Стек
- **Backend**: FastAPI + PostgreSQL + SQLAlchemy (async)
- **Frontend**: Vue 3 + TypeScript + Vite + Tailwind CSS
- **AI**: Claude API (или Ollama локально)
- **Auth**: JWT tokens

## 5 типов заданий
- 🧪 **Тест** — адаптивный (easy/medium/hard)
- ⚔️ **Баттл** — дискуссия двух сторон
- 🔍 **Анализ** — открытый ответ на кейс
- 🎴 **Карточки** — флеш-карты с самооценкой
- 📝 **Пересказ** — синтез материала
