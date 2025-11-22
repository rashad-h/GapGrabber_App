# Demo Notes - GapGrabber Backend

## Demo WhatsApp Number
Set `TEST_WHATSAPP_NUMBER` in your `.env` file (e.g., `+1234567890`)

## Quick Demo Flow

### 1. Start the Server
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 2. Trigger a Campaign
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

This will:
- ✅ Evaluate customers with OpenAI
- ✅ Generate personalized messages
- ✅ Send WhatsApp to top 3 customers
- ✅ Schedule next batch automatically

### 3. Check Campaign Status
```bash
curl http://localhost:8000/api/campaigns/1 | python3 -m json.tool
```

### 4. View Messages
```bash
curl http://localhost:8000/api/messages | python3 -m json.tool
```

## API Endpoints for Demo

- `GET /health` - Health check
- `POST /api/slots/fill` - Trigger campaign
- `GET /api/appointments` - View appointments
- `GET /api/messages` - View conversations
- `GET /api/campaigns/{id}` - Campaign details
- `POST /webhooks/twilio` - Receive WhatsApp (needs ngrok)

## Swagger UI
Visit: http://localhost:8000/docs

## Webhook Setup (for receiving messages)

1. Start ngrok: `ngrok http 8000`
2. Configure in Twilio Console:
   - URL: `https://your-ngrok-url.ngrok.io/webhooks/twilio`
   - Method: POST

## Demo Highlights

✅ **AI-Powered Personalization** - Every message is unique
✅ **Automatic Cascade** - Sends to next batch if no response
✅ **Immediate Responses** - Webhook handles customer replies instantly
✅ **Smart Evaluation** - OpenAI ranks best customers to contact

