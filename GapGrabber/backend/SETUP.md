# Setup Instructions

## Quick Start

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**

   Option A: Create `.env` file in backend directory:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

   Option B: Use parent directory's `secrets.env`:
   ```bash
   # The config will automatically check ../secrets.env
   # Just make sure it has all required variables
   ```

5. **Initialize database with seed data:**
```bash
python seed_data.py
```

6. **Start the server:**
```bash
uvicorn main:app --reload --port 8000
```

## Environment Variables Required

- `OPENAI_API_KEY` - Your OpenAI API key
- `TWILIO_ACCOUNT_SID` - Twilio Account SID
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token  
- `TWILIO_WHATSAPP_NUMBER` - Your Twilio WhatsApp number (format: whatsapp:+1234567890)
- `DATABASE_URL` - SQLite database URL (default: sqlite:///./database.db)
- `LOG_LEVEL` - Logging level (default: INFO)

## Testing the API

Once the server is running, test the slot fill endpoint:

```bash
curl -X POST http://localhost:8000/api/slots/fill \
  -H "Content-Type: application/json" \
  -d '{
    "cancelled_slot_time": "2025-11-23T14:00:00Z",
    "service_type": "haircut",
    "discount_percentage": 10,
    "wait_time_minutes": 1,
    "custom_context": "My lunch slot opened up last minute!"
  }'
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

