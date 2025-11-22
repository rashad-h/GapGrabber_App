# Dashboard API Testing Flow

This guide shows the API flow that mimics what a dashboard would do.

---

## 🎯 Complete Dashboard Flow

### Step 1: Dashboard Loads - View Schedule
**What dashboard does:** Shows all upcoming appointments

**API Call:**
```
GET http://localhost:8000/api/appointments?status=scheduled
```

**Expected Response:**
```json
{
  "appointments": [
    {
      "id": 1,
      "customer": {"id": 1, "name": "Sarah Johnson", "phone": "+1234567890"},
      "scheduled_time": "2025-11-25T10:00:00Z",
      "service_type": "haircut",
      "status": "scheduled"
    },
    ...
  ]
}
```

**Postman:** Use "Get Appointments" request

---

### Step 2: User Cancels Appointment - Triggers Fill Campaign
**What dashboard does:** User clicks "Cancel & Fill Slot" button on an appointment

**API Call:**
```
POST http://localhost:8000/api/appointments/{appointment_id}/cancel-and-fill
Content-Type: application/json

{
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "Customer cancelled last minute - emergency slot available!"
}
```

**Example:**
```
POST http://localhost:8000/api/appointments/1/cancel-and-fill
Body: {
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "Customer cancelled last minute - emergency slot available!"
}
```

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
      "message_sent": "Hi Sarah! Hope you're doing well..."
    }
  ]
}
```

**Save `campaign_id` from response!** (e.g., `campaign_id: 1`)

**Postman:** Use "Trigger Slot Fill Campaign" request

---

### Step 3: Dashboard Shows Campaign Status
**What dashboard does:** Displays campaign progress, who was contacted, status

**API Call:**
```
GET http://localhost:8000/api/campaigns/1
```
(Replace `1` with your `campaign_id`)

**Expected Response:**
```json
{
  "id": 1,
  "status": "active",
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "discount_percentage": 10,
  "wait_time_minutes": 1,
  "custom_context": "My lunch slot opened up last minute!",
  "current_batch": 1,
  "total_contacted": 3,
  "outreach_attempts": [
    {
      "customer": {"name": "Sarah Johnson", "phone": "+1234567890"},
      "status": "sent",
      "batch_number": 1,
      "message_sent": "Hi Sarah!...",
      "sent_at": "2025-11-22T15:00:00Z",
      "responded_at": null
    }
  ]
}
```

**Postman:** Use "Get Campaign Details" request (update campaign_id variable)

---

### Step 4: Dashboard Shows Conversations
**What dashboard does:** Shows message threads with customers

**API Call:**
```
GET http://localhost:8000/api/messages?campaign_id=1
```
(Replace `1` with your `campaign_id`)

**Expected Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "customer": {"id": 1, "name": "Sarah Johnson", "phone": "+1234567890"},
      "direction": "outbound",
      "content": "Hi Sarah! Hope you're doing well...",
      "timestamp": "2025-11-22T15:00:00Z"
    },
    {
      "id": 2,
      "customer": {"id": 1, "name": "Sarah Johnson", "phone": "+1234567890"},
      "direction": "inbound",
      "content": "Yes, I can do tomorrow at 2pm!",
      "timestamp": "2025-11-22T15:03:00Z"
    },
    {
      "id": 3,
      "customer": {"id": 1, "name": "Sarah Johnson", "phone": "+1234567890"},
      "direction": "outbound",
      "content": "Perfect! Confirmed for tomorrow at 2pm...",
      "timestamp": "2025-11-22T15:03:01Z"
    }
  ]
}
```

**Postman:** Use "Get Messages" request (add `campaign_id` query param)

---

### Step 5: Dashboard Refreshes - Check Updated Appointments
**What dashboard does:** After customer accepts, refresh to see updated schedule

**API Call:**
```
GET http://localhost:8000/api/appointments
```

**Expected Response:** Should show the appointment time updated for the customer who accepted

---

### Step 6: (Optional) Simulate Customer Response
**What dashboard does:** In real flow, webhook receives this automatically

**API Call:**
```
POST http://localhost:8000/webhooks/twilio
Content-Type: application/x-www-form-urlencoded

From=whatsapp:+1234567890
Body=Yes, I can do tomorrow at 2pm!
MessageSid=SMtest123
```

**Then refresh Step 3 and Step 4** to see updated status and new messages

---

## 📋 Complete Testing Sequence

### Quick Test Flow (Copy-paste ready):

1. **View Schedule**
   ```
   GET /api/appointments?status=scheduled
   ```

2. **Trigger Campaign** (Save campaign_id from response)
   ```
   POST /api/appointments/{appointment_id}/cancel-and-fill
   Body: {
     "discount_percentage": 10,
     "wait_time_minutes": 1,
     "custom_context": "Customer cancelled last minute - emergency slot available!"
   }
   ```
   
   Example: `POST /api/appointments/1/cancel-and-fill`

3. **Check Campaign Status** (Use campaign_id from step 2)
   ```
   GET /api/campaigns/1
   ```

4. **View Messages**
   ```
   GET /api/messages?campaign_id=1
   ```

5. **Simulate Customer Response** (Optional)
   ```
   POST /webhooks/twilio
   Body (form-urlencoded):
     From=whatsapp:+1234567890
     Body=Yes, I can do tomorrow at 2pm!
     MessageSid=SMtest123
   ```

6. **Refresh Campaign Status** (See updated status)
   ```
   GET /api/campaigns/1
   ```

7. **Refresh Messages** (See new conversation)
   ```
   GET /api/messages?campaign_id=1
   ```

8. **Refresh Appointments** (See updated schedule)
   ```
   GET /api/appointments
   ```

---

## 🎨 Dashboard UI Mapping

| Dashboard Action | API Endpoint |
|-----------------|--------------|
| Load page | `GET /api/appointments` |
| Show campaign list | `GET /api/campaigns/{id}` (for each campaign) |
| Click "Cancel & Fill Slot" on appointment | `POST /api/appointments/{id}/cancel-and-fill` |
| Show campaign details | `GET /api/campaigns/{id}` |
| Display message threads | `GET /api/messages?campaign_id={id}` |
| Show customer conversations | `GET /api/messages?customer_id={id}` |
| Refresh schedule | `GET /api/appointments` |
| Auto-update (polling) | `GET /api/campaigns/{id}` every 5 seconds |

---

## 🔄 Real-Time Updates (For Dashboard)

The dashboard would poll these endpoints:

1. **Campaign Status** - Poll every 5 seconds:
   ```
   GET /api/campaigns/{campaign_id}
   ```
   Check `status` field: `"active"`, `"filled"`, or `"expired"`

2. **New Messages** - Poll every 3 seconds:
   ```
   GET /api/messages?campaign_id={campaign_id}
   ```
   Compare `timestamp` to detect new messages

3. **Appointment Updates** - Poll every 10 seconds:
   ```
   GET /api/appointments
   ```
   Compare `scheduled_time` to detect changes

---

## 📝 Postman Collection Variables

Set these in Postman environment:

- `base_url` = `http://localhost:8000`
- `campaign_id` = `1` (update after triggering campaign)
- `customer_id` = `1` (for filtering)

---

## 🎯 Demo Flow Summary

**For Hackathon Demo:**

1. **Show Schedule** → `GET /api/appointments` (see plumber appointments)
2. **Cancel Appointment** → `POST /api/appointments/{id}/cancel-and-fill` (triggers campaign)
3. **Show Campaign** → `GET /api/campaigns/{id}` (see personalized messages to customers)
4. **Show Messages** → `GET /api/messages?campaign_id={id}` (see AI-generated messages)
5. **Simulate Response** → `POST /webhooks/twilio` (customer accepts)
6. **Show Updated** → `GET /api/campaigns/{id}` (status = "filled")
7. **Show Final Messages** → `GET /api/messages?campaign_id={id}` (see confirmation)
8. **Show Updated Schedule** → `GET /api/appointments` (appointment rescheduled)

This demonstrates the full autonomous flow!

