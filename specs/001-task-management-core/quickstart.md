# Quickstart: Core Task Management

## Local Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+

### Steps

1. **Clone and Setup Environment**
   ```bash
   cp .env.example .env
   # Update NEON_DATABASE_URL and JWT_SECRET
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn src.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Running with Docker**
   ```bash
   docker-compose up --build
   ```

## Testing

- **Backend:** `pytest`
- **Frontend/E2E:** `npx playwright test`
