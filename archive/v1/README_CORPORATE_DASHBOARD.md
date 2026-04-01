# Corporate Deep-Scrape Dashboard

A production-grade React + FastAPI application for on-demand civic health analysis.

## Features
- **Deep Scraping**: Real-time collection from Global News + Reddit.
- **Async Processing**: Job-based execution with live progress tracking (Server-Sent Events).
- **Grounded Chat**: Ask questions about specific cities; answers are strictly cited from the fresh scrape.
- **Fairness**: Balanced document selection and transparent citation of all sources.

## Architecture
- **Backend**: FastAPI (Python), SQLite (Job DB), BackgroundTasks for scraping pipeline.
- **Frontend**: React (Vite), Tailwind CSS, SSE for real-time updates.

## Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API Key

### Backend
1. Navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: If you have issues with `lxml` or `uvicorn`, ensure your python environment is clean.*

3. Run the server:
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   python3 -m app.main
   ```
   Server runs at `http://0.0.0.0:8000`.

### Frontend
1. Navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start development server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:5173`.

## Usage
1. Select target cities (e.g., "London", "New York").
2. (Optional) Select specific dimensions (e.g., "Safety", "Housing").
3. Choose "Standard" or "Deep Scrape".
4. Click **Start Analysis**.
5. Watch the live progress log.
6. View results with score breakdowns and citations.
7. Use the chat window to ask specific questions like "What are the specific housing policies mentioned for London?".

## key Files
- `backend/app/jobs/pipeline.py`: The core scraping/scoring logic.
- `backend/app/scrape/`: Modular scraping functions (News, Reddit).
- `frontend/src/App.tsx`: Main UI layout and logic.
- `frontend/src/components/Chat.tsx`: AI chat interface.
