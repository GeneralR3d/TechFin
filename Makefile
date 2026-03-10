.PHONY: dev frontend backend

dev:
	@bash start.sh

frontend:
	cd frontend && npm run dev

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000
