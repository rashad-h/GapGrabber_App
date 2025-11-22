# Testing Guide for GapGrabber Backend

## Quick Start Testing

### Step 1: Set Up Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=sk-your-key-here
TWILIO_ACCOUNT_SID=ACyour-sid-here
TWILIO_AUTH_TOKEN=your-token-here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
DATABASE_URL=sqlite:///./database.db
LOG_LEVEL=INFO
```

**Note:** For initial testing without Twilio, you can use dummy values. The API will work except for actual WhatsApp sending.

### Step 3: Initialize Database

```bash
python seed_data.py
```

This creates:
- 10 sample customers
- Multiple appointments (past and future)
- Some message history

### Step 4: Start the Server

```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application started
INFO:     APScheduler started
```

### Step 5: Test the API

#### Option A: Use the Test Script

```bash
./test_api.sh
```

#### Option B: Manual Testing

**1. Health Check:**
```bash
curl http://localhost:8000/health
```

**2. Get Appointments:**
```bash
curl http://localhost:8000/api/appointments | python3 -m json.tool
```

**3. Get Messages:**
```bash
curl http://localhost:8000/api/messages | python3 -m json.tool
```

**4. Trigger Slot Fill Campaign:**
```bash
curl -X POST http://localhost:8000/api/slots/fill \
  -H "Content-Type: application/json" \
  -d '{
    "cancelled_slot_time": "2025-11-23T14:00:00Z",
    "service_type": "haircut",
    "discount_percentage": 10,
    "wait_time_minutes": 1,
    "custom_context": "My lunch slot opened up last minute!"
  }' | python3 -m json.tool
```

**5. Get Campaign Details:**
```bash
# Replace 123 with the campaign_id from step 4
curl http://localhost:8000/api/campaigns/123 | python3 -m json.tool
```

**6. Get Messages for Campaign:**
```bash
curl "http://localhost:8000/api/messages?campaign_id=123" | python3 -m json.tool
```

#### Option C: Use Swagger UI (Recommended)

Open your browser and go to:
```
http://localhost:8000/docs
```

This provides an interactive API documentation where you can:
- See all endpoints
- Test them directly
- View request/response schemas

## Testing the Full Flow

### 1. Trigger a Campaign

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

**Expected Result:**
- Campaign created with status "active"
- Top 3 customers evaluated and contacted
- Personalized messages generated and sent (if Twilio configured)
- Next batch scheduled for 1 minute later

### 2. Check Campaign Status

```bash
curl http://localhost:8000/api/campaigns/1 | python3 -m json.tool
```

**Expected Result:**
- Campaign details
- List of outreach attempts
- Current batch number
- Status of each customer contact

### 3. Simulate Customer Response (Webhook)

To test the webhook without actual Twilio:

```bash
curl -X POST http://localhost:8000/webhooks/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890&Body=Yes, I can do tomorrow at 2pm!&MessageSid=SMtest123"
```

**Expected Result:**
- Message saved to database
- Intent analyzed (accept/decline/unclear)
- Personalized response generated
- If accepted: slot filled, others notified

### 4. Verify Database Changes

Check the database file:
```bash
sqlite3 database.db "SELECT * FROM slot_fill_campaigns;"
sqlite3 database.db "SELECT * FROM campaign_outreach;"
sqlite3 database.db "SELECT * FROM messages ORDER BY timestamp DESC LIMIT 10;"
```

## Testing Without Twilio

If you don't have Twilio set up yet, you can still test:

1. **API endpoints** - All work except actual WhatsApp sending
2. **OpenAI integration** - Message generation works
3. **Campaign logic** - Full orchestration works
4. **Database operations** - All CRUD operations work

The only thing that won't work is actual WhatsApp message delivery. You'll see errors in logs like:
```
Failed to send WhatsApp message: ...
```

But the campaign logic will still execute and save to the database.

## Common Issues

### Issue: ModuleNotFoundError
**Solution:** Make sure you're in the `backend` directory and virtual environment is activated.

### Issue: Database errors
**Solution:** Run `python seed_data.py` to initialize the database.

### Issue: OpenAI API errors
**Solution:** Check your `OPENAI_API_KEY` in `.env` file.

### Issue: Port already in use
**Solution:** Change port: `uvicorn main:app --reload --port 8001`

## Next Steps

1. ✅ Test all API endpoints
2. ✅ Verify campaign creation and tracking
3. 🔄 Set up Twilio WhatsApp sandbox for real messaging
4. 🔄 Test webhook with actual WhatsApp messages
5. 🔄 Connect Lovable frontend to backend

## API Endpoints Summary

| Endpoint | Method | Purpose |
|---------|--------|---------|
| `/health` | GET | Health check |
| `/api/slots/fill` | POST | Trigger slot fill campaign |
| `/api/appointments` | GET | Get all appointments |
| `/api/messages` | GET | Get conversation history |
| `/api/campaigns/{id}` | GET | Get campaign details |
| `/webhooks/twilio` | POST | Receive WhatsApp messages |

