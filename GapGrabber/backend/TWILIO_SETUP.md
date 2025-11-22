# Twilio WhatsApp Integration - Setup Guide

## ✅ Status: Twilio Account Verified

Your Twilio account is **active and valid**:
- Account Name: My first Twilio account
- Status: active
- WhatsApp Number: +447492542446

## 🧪 Testing the Integration

### Option 1: Test via Script

```bash
cd backend
source venv/bin/activate
python test_twilio_integration.py +1234567890
```

Replace `+1234567890` with a WhatsApp number that's registered with Twilio.

### Option 2: Test via API

Start the server:
```bash
uvicorn main:app --reload --port 8000
```

Then trigger a campaign (this will send real WhatsApp messages):
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

This will:
1. Evaluate customers with OpenAI
2. Generate personalized messages
3. **Send WhatsApp messages to top 3 customers**

## 📱 Twilio WhatsApp Sandbox Setup

If you're using Twilio's WhatsApp sandbox:

1. **Join the sandbox:**
   - Send `JOIN <your-code>` to `+1 415 523 8846`
   - You'll receive a confirmation message

2. **Add your number to Twilio:**
   - Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message
   - Add your number to the sandbox

3. **Test sending:**
   ```bash
   python test_twilio_integration.py +your_whatsapp_number
   ```

## 🔗 Webhook Configuration

To receive incoming WhatsApp messages:

1. **Get your webhook URL:**
   - If running locally: Use ngrok or similar: `ngrok http 8000`
   - If deployed: Use your production URL

2. **Configure in Twilio Console:**
   - Go to: Console → Messaging → Settings → WhatsApp Sandbox Settings
   - Set "When a message comes in" to: `https://your-url.com/webhooks/twilio`
   - Set HTTP method: `POST`

3. **Test webhook:**
   - Send a WhatsApp message to your Twilio number
   - Check server logs to see the webhook being called

## ✅ What's Working

- ✅ Twilio account validated
- ✅ Client initialized
- ✅ `send_whatsapp_message()` function ready
- ✅ Webhook handler endpoint ready
- ✅ Signature verification ready

## 🚀 Next Steps

1. **Test sending:** Use the test script or trigger a campaign
2. **Configure webhook:** Set up webhook URL in Twilio console
3. **Test receiving:** Send a message and verify webhook works
4. **Full flow:** Trigger campaign → Send messages → Receive responses → Process automatically

## 📝 Notes

- The backend will automatically send WhatsApp messages when campaigns are triggered
- Messages are personalized using OpenAI
- Responses are handled automatically via webhook
- All messages are stored in the database

