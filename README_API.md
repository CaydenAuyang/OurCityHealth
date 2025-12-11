# Business Portfolio API Proxy

This backend proxy server handles OpenAI API calls for the business portfolio chatbot interface, using your API key securely.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

Or on Windows:
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

3. Start the API proxy server:
```bash
python api_proxy.py
```

The server will start on `http://localhost:5000` by default.

## Usage

The frontend (`business_portfolio.html`) will automatically call `/api/chat` endpoint when users interact with the chatbot.

## Endpoints

- `POST /api/chat` - Proxy for OpenAI chat completions
- `GET /health` - Health check endpoint

## Environment Variables

- `OPENAI_API_KEY` (required) - Your OpenAI API key
- `PORT` (optional) - Server port (default: 5000)

## Security Notes

- The API key is stored server-side only, never exposed to clients
- CORS is enabled for the frontend
- All API calls are proxied through your server, allowing you to:
  - Monitor usage
  - Implement rate limiting
  - Add authentication/authorization
  - Charge clients for API usage




