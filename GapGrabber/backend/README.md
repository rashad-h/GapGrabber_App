# GapGrabber Backend

FastAPI backend for autonomous slot-filling with WhatsApp and OpenAI.

## Setup

1. **Install dependencies:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Initialize database:**
```bash
python seed_data.py
```

4. **Run the server:**
```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `POST /api/slots/fill` - Trigger slot fill campaign
- `GET /api/appointments` - Get all appointments
- `GET /api/messages` - Get conversation history
- `GET /api/campaigns/{campaign_id}` - Get campaign details
- `POST /webhooks/twilio` - Twilio webhook for incoming messages

## Testing

Use the seed script to populate test data, then trigger a campaign:

```bash
curl -X POST http://localhost:8000/api/slots/fill \
  -H "Content-Type: application/json" \
  -d '{
    "cancelled_slot_time": "2025-11-23T14:00:00Z",
    "service_type": "haircut",
    "discount_percentage": 10,
    "wait_time_minutes": 1,
    "custom_context": "My lunch slot opened up!"
  }'
```

