# Postman Testing Guide - GapGrabber Backend

## Setup

1. **Start the server:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

2. **Base URL:** `http://localhost:8000`

3. **Import Collection:** You can manually create requests or use the examples below

---

## API Endpoints

### 1. Health Check

**GET** `http://localhost:8000/health`

**Headers:** None required

**Expected Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Get All Appointments

**GET** `http://localhost:8000/api/appointments`

**Query Parameters (optional):**
- `status` - Filter by status (scheduled, cancelled, completed)
- `from_date` - Start date (ISO format)
- `to_date` - End date (ISO format)

**Example:**
```
GET http://localhost:8000/api/appointments?status=scheduled
```

**Expected Response:**
```json
{
  "appointments": [
    {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "Sarah Johnson",
        "phone": "+1234567890"
      },
      "scheduled_time": "2025-11-25T10:00:00Z",
      "service_type": "haircut",
      "status": "scheduled"
    }
  ]
}
```

---

### 3. Trigger Slot Fill Campaign ⭐ MAIN ENDPOINT

**POST** `http://localhost:8000/api/slots/fill`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "service_type": "haircut",
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "One of my regular customers cancelled last minute - it's my lunch break slot so would be great to fill it!"
}
```

**Field Descriptions:**
- `cancelled_slot_time` - ISO datetime string (when the slot opened)
- `service_type` - Type of service (e.g., "haircut", "hair color")
- `discount_percentage` - Discount to offer (0-100)
- `wait_time_minutes` - How long to wait before sending next batch
- `custom_context` - Optional: Business owner's context for personalization

**Expected Response:**
```json
{
  "campaign_id": 1,
  "candidates_evaluated": 15,
  "initial_batch_sent": 3,
  "wait_time_minutes": 1,
  "customers_contacted": [
    {
      "id": 1,
      "name": "Sarah Johnson",
      "phone": "+1234567890",
      "message_sent": "Hi Sarah! Hope you're doing well. One of my regulars just cancelled their slot tomorrow at 2pm - I know you have an appointment next week, would you like to come in earlier? I can offer 10% off for the flexibility! 😊"
    }
  ]
}
```

**What Happens:**
1. Creates campaign in database
2. Finds customers with future appointments (7-14 days out)
3. Uses OpenAI to evaluate and rank customers
4. Generates personalized messages for top 3
5. Sends WhatsApp messages
6. Schedules next batch automatically

---

### 4. Get Campaign Details

**GET** `http://localhost:8000/api/campaigns/{campaign_id}`

**Example:**
```
GET http://localhost:8000/api/campaigns/1
```

**Expected Response:**
```json
{
  "id": 1,
  "status": "active",
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "One of my regulars cancelled...",
  "current_batch": 1,
  "total_contacted": 3,
  "outreach_attempts": [
    {
      "customer": {
        "id": 1,
        "name": "Sarah Johnson",
        "phone": "+1234567890"
      },
      "status": "sent",
      "batch_number": 1,
      "message_sent": "Hi Sarah! Hope you're doing well...",
      "sent_at": "2025-11-22T15:00:00Z",
      "responded_at": null
    }
  ]
}
```

---

### 5. Get Messages/Conversations

**GET** `http://localhost:8000/api/messages`

**Query Parameters (optional):**
- `customer_id` - Filter by customer ID
- `campaign_id` - Filter by campaign ID

**Examples:**
```
GET http://localhost:8000/api/messages
GET http://localhost:8000/api/messages?customer_id=1
GET http://localhost:8000/api/messages?campaign_id=1
```

**Expected Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "Sarah Johnson",
        "phone": "+1234567890"
      },
      "direction": "outbound",
      "content": "Hi Sarah! Hope you're doing well...",
      "timestamp": "2025-11-22T15:00:00Z"
    },
    {
      "id": 2,
      "customer": {
        "id": 1,
        "name": "Sarah Johnson",
        "phone": "+1234567890"
      },
      "direction": "inbound",
      "content": "Yes, I can do tomorrow at 2pm!",
      "timestamp": "2025-11-22T15:03:00Z"
    }
  ]
}
```

---

### 6. Webhook Endpoint (for Twilio)

**POST** `http://localhost:8000/webhooks/twilio`

**Note:** This is typically called by Twilio, but you can test it manually.

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
```

**Body (form-urlencoded):**
```
From=whatsapp:+1234567890
Body=Yes, I can do tomorrow at 2pm!
MessageSid=SMtest123
```

**Expected Response:**
```json
{
  "status": "ok"
}
```

---

## Complete Testing Flow

### Step 1: Check Health
```
GET http://localhost:8000/health
```

### Step 2: View Existing Appointments
```
GET http://localhost:8000/api/appointments
```

### Step 3: Trigger a Campaign
```
POST http://localhost:8000/api/slots/fill
Body: {
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "service_type": "haircut",
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "My lunch slot opened up!"
}
```

**Save the `campaign_id` from the response!**

### Step 4: Check Campaign Status
```
GET http://localhost:8000/api/campaigns/{campaign_id}
```

### Step 5: View Generated Messages
```
GET http://localhost:8000/api/messages?campaign_id={campaign_id}
```

### Step 6: Simulate Customer Response (Optional)
```
POST http://localhost:8000/webhooks/twilio
Body (form-urlencoded):
  From=whatsapp:+1234567890
  Body=Yes, I can do tomorrow at 2pm!
  MessageSid=SMtest123
```

### Step 7: Check Updated Campaign Status
```
GET http://localhost:8000/api/campaigns/{campaign_id}
```

---

## Postman Collection JSON

You can import this into Postman:

```json
{
  "info": {
    "name": "GapGrabber Backend",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "Get Appointments",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/appointments",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "appointments"]
        }
      }
    },
    {
      "name": "Trigger Slot Fill Campaign",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"cancelled_slot_time\": \"2025-11-23T14:00:00Z\",\n  \"service_type\": \"haircut\",\n  \"discount_percentage\": 10,\n  \"wait_time_minutes\": 1,\n  \"custom_context\": \"My lunch slot opened up last minute!\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/api/slots/fill",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "slots", "fill"]
        }
      }
    },
    {
      "name": "Get Campaign Details",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/campaigns/1",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "campaigns", "1"]
        }
      }
    },
    {
      "name": "Get Messages",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/messages",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "messages"]
        }
      }
    }
  ]
}
```

---

## Tips

1. **Use Environment Variables in Postman:**
   - Create an environment with `base_url = http://localhost:8000`
   - Use `{{base_url}}/api/slots/fill` in requests

2. **Save Campaign ID:**
   - After triggering a campaign, save the `campaign_id` from response
   - Use it in subsequent requests to check status

3. **Test Different Scenarios:**
   - Different service types
   - Different discount percentages
   - Different wait times
   - With/without custom_context

4. **Check Swagger UI:**
   - Visit `http://localhost:8000/docs` for interactive API docs
   - Test endpoints directly in browser

---

## Common Issues

**Error: Connection refused**
- Make sure server is running on port 8000

**Error: Validation error**
- Check date format (must be ISO 8601: `2025-11-23T14:00:00Z`)
- Ensure all required fields are present

**No customers contacted**
- Run `python seed_data.py` to populate database
- Check that customers have future appointments matching service_type

