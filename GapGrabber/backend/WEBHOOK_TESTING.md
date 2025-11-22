# Testing the Twilio Webhook

## How to Simulate Customer Response

The webhook endpoint receives WhatsApp messages from customers and processes them automatically.

### Endpoint
```
POST http://localhost:8000/webhooks/twilio
```

### Request Format

**Content-Type:** `application/x-www-form-urlencoded`

**Body (form-urlencoded):**
```
From=whatsapp:+1234567890
Body=Yes, I can do tomorrow at 2pm!
MessageSid=SMtest123456
```

### Testing in Postman

1. **Method:** POST
2. **URL:** `http://localhost:8000/webhooks/twilio`
3. **Headers:**
   - `Content-Type: application/x-www-form-urlencoded`
4. **Body:** Select `x-www-form-urlencoded` and add:
   - `From` = `whatsapp:+1234567890` (use your TEST_WHATSAPP_NUMBER from .env)
   - `Body` = `Yes, I can do tomorrow at 2pm!` (or any response)
   - `MessageSid` = `SMtest123456`

### Testing with cURL

```bash
curl -X POST http://localhost:8000/webhooks/twilio \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=whatsapp:+1234567890" \
  -d "Body=Yes, I can do tomorrow at 2pm!" \
  -d "MessageSid=SMtest123456"
```

### Example Responses to Test

**Accept:**
```
Body=Yes, I can do tomorrow at 2pm!
Body=That works for me!
Body=Perfect, I'll be there!
Body=Yes please!
```

**Decline:**
```
Body=No thanks, I'll keep my original appointment
Body=Sorry, can't make it
Body=Not interested
```

**Unclear:**
```
Body=Maybe, let me check
Body=What time again?
Body=Can you tell me more?
```

### What Happens

1. Webhook receives the message
2. Finds customer by phone number (from TEST_WHATSAPP_NUMBER env var)
3. Checks if they have an active campaign
4. Uses OpenAI to analyze intent (accept/decline/unclear)
5. Generates personalized response
6. Sends WhatsApp reply immediately
7. If accepted: fills slot, notifies others, ends campaign
8. If declined: marks declined, campaign continues
9. If unclear: asks for clarification

### Testing Flow

1. **Cancel an appointment** → Creates campaign
2. **Check campaign** → See who was contacted
3. **Send webhook** → Simulate customer response
4. **Check campaign again** → See updated status
5. **Check messages** → See the conversation

### Important Notes

- The phone number (`From`) must match a customer in your database
- The customer must have an active campaign outreach
- The webhook always returns `200 OK` (even on errors) to prevent Twilio retries
- Check server logs to see detailed processing

