<!-- e6696e47-33ad-4718-b69e-64b87c704d58 aa1f8cf2-ac33-4eef-95ca-c968f376647d -->
# GapGrabber Backend - Complete Implementation Plan

## Architecture Overview

**Stack:** Python 3.11+ | FastAPI | SQLite | Twilio WhatsApp | OpenAI | APScheduler

**Core Flow:**

1. Business owner triggers slot fill with discount %, wait time, and optional custom context
2. Backend finds customers with future bookings
3. OpenAI evaluates customers based on message history
4. **OpenAI generates personalized messages** for each customer (referencing their name, chat history, custom context)
5. Send personalized WhatsApp messages to top 3 candidates simultaneously
6. **Webhook responds IMMEDIATELY when customer replies** with LLM-generated response
7. APScheduler waits [configurable time], then sends to next batch with fresh personalized messages
8. Previous customers stay active (can still respond late)
9. First customer to accept wins the slot
10. Repeat until slot is filled

---

## Database Schema (SQLite)

### Table: `customers`

- `id` (INTEGER PRIMARY KEY)
- `phone_number` (TEXT UNIQUE)
- `name` (TEXT)
- `created_at` (TIMESTAMP)

### Table: `appointments`

- `id` (INTEGER PRIMARY KEY)
- `customer_id` (INTEGER FK)
- `scheduled_time` (TIMESTAMP)
- `service_type` (TEXT)
- `status` (TEXT: 'scheduled', 'cancelled', 'completed')
- `created_at` (TIMESTAMP)

### Table: `messages`

- `id` (INTEGER PRIMARY KEY)
- `customer_id` (INTEGER FK)
- `direction` (TEXT: 'inbound', 'outbound')
- `content` (TEXT)
- `timestamp` (TIMESTAMP)
- `twilio_sid` (TEXT)

### Table: `slot_fill_campaigns`

- `id` (INTEGER PRIMARY KEY)
- `cancelled_slot_time` (TIMESTAMP)
- `service_type` (TEXT)
- `discount_percentage` (INTEGER)
- `wait_time_minutes` (INTEGER)
- `custom_context` (TEXT, nullable) - **NEW: business owner's optional context/prompt**
- `status` (TEXT: 'active', 'filled', 'expired')
- `filled_by_customer_id` (INTEGER FK, nullable)
- `created_at` (TIMESTAMP)

### Table: `campaign_outreach`

- `id` (INTEGER PRIMARY KEY)
- `campaign_id` (INTEGER FK)
- `customer_id` (INTEGER FK)
- `batch_number` (INTEGER)
- `message_sent` (TEXT) - **NEW: stores the personalized message that was sent**
- `status` (TEXT: 'sent', 'accepted', 'declined', 'notified_filled')
- `sent_at` (TIMESTAMP)
- `responded_at` (TIMESTAMP, nullable)

---

## API Endpoints Specification

### 1. `POST /api/slots/fill`

**Purpose:** Trigger slot fill campaign (called by Lovable dashboard)

**Request Body:**

```json
{
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "service_type": "haircut",
  "discount_percentage": 10,
  "wait_time_minutes": 30,
  "custom_context": "One of my regular customers cancelled last minute - it's my lunch break slot so would be great to fill it!"
}
```

**Note:** `custom_context` is optional - business owner can add personal context that will be used to personalize messages

**Response:**

```json
{
  "campaign_id": 123,
  "candidates_evaluated": 15,
  "initial_batch_sent": 3,
  "wait_time_minutes": 30,
  "customers_contacted": [
    {
      "id": 45,
      "name": "Sarah Johnson",
      "phone": "+1234567890",
      "message_sent": "Hi Sarah! Hope you're doing well. One of my regulars just cancelled their slot tomorrow at 2pm - I know you have an appointment next week, would you like to come in earlier? I can offer 10% off for the flexibility! 😊"
    }
  ]
}
```

**Logic:**

1. Create campaign in DB with custom_context
2. Query customers with future appointments (7-14 days out)
3. Call OpenAI to evaluate based on message history
4. **For each top 3: Generate personalized message with OpenAI**
5. Send personalized WhatsApp messages
6. Schedule `send_next_batch` job for +[wait_time_minutes]
7. Return response

---

### 2. `POST /webhooks/twilio`

**Purpose:** Receive incoming WhatsApp messages from Twilio

**Request Body:** (Twilio standard webhook format)

```
From=whatsapp:+1234567890
Body=Yes, I can do tomorrow at 2pm!
MessageSid=SMxxxxxxxxx
```

**Response:** `200 OK` (must respond fast) + immediate personalized WhatsApp reply

**Logic (CRITICAL - IMMEDIATE RESPONSE):**

1. Verify Twilio signature
2. Save message to DB
3. Check if customer has active campaign outreach
4. Use OpenAI to determine sentiment (accept/decline/question)
5. **Generate personalized response with OpenAI** (reference conversation history)
6. **IF ACCEPTED:**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Check campaign still active (race condition check)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Mark outreach as 'accepted'
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Fill the slot in appointments table
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Mark campaign as 'filled'
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - **IMMEDIATELY send personalized WhatsApp confirmations:**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - To accepter: LLM-generated confirmation (warm, personal, references their response)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - To all other active outreach: LLM-generated "slot filled" messages
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Cancel all scheduled jobs for this campaign

7. **IF DECLINED:**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Mark outreach as 'declined'
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - **IMMEDIATELY send personalized WhatsApp:** LLM-generated acknowledgment
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - Campaign continues (next batch will still be sent)

8. **IF UNCLEAR/QUESTION:**

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - **IMMEDIATELY send personalized WhatsApp:** LLM-generated clarification

---

### 3. `GET /api/appointments`

**Purpose:** Get all appointments (for Lovable dashboard)

**Query Params:**

- `status` (optional): filter by status
- `from_date` (optional): start date
- `to_date` (optional): end date

**Response:**

```json
{
  "appointments": [
    {
      "id": 123,
      "customer": {"id": 45, "name": "Sarah", "phone": "+123"},
      "scheduled_time": "2025-11-25T10:00:00Z",
      "service_type": "haircut",
      "status": "scheduled"
    }
  ]
}
```

---

### 4. `GET /api/campaigns/{campaign_id}`

**Purpose:** Get campaign status and outreach details

**Response:**

```json
{
  "id": 123,
  "status": "active",
  "cancelled_slot_time": "2025-11-23T14:00:00Z",
  "discount_percentage": 10,
  "wait_time_minutes": 30,
  "custom_context": "One of my regulars cancelled...",
  "current_batch": 2,
  "total_contacted": 6,
  "outreach_attempts": [
    {
      "customer": {"name": "Sarah", "phone": "+123"},
      "status": "sent",
      "batch_number": 1,
      "message_sent": "Hi Sarah! Hope you're doing well...",
      "sent_at": "2025-11-22T15:00:00Z"
    }
  ]
}
```

---

### 5. `GET /api/messages`

**Purpose:** Get conversation history (for Lovable dashboard)

**Query Params:**

- `customer_id` (optional): filter by customer
- `campaign_id` (optional): filter by campaign

**Response:**

```json
{
  "messages": [
    {
      "id": 456,
      "customer": {"id": 45, "name": "Sarah"},
      "direction": "outbound",
      "content": "Hi Sarah! Hope you're doing well. One of my regulars just cancelled their slot tomorrow at 2pm...",
      "timestamp": "2025-11-22T15:00:00Z"
    },
    {
      "id": 457,
      "customer": {"id": 45, "name": "Sarah"},
      "direction": "inbound",
      "content": "Yes please! That works perfect for me",
      "timestamp": "2025-11-22T15:03:00Z"
    },
    {
      "id": 458,
      "customer": {"id": 45, "name": "Sarah"},
      "direction": "outbound",
      "content": "Awesome Sarah! You're all set for tomorrow at 2pm with 10% off. Looking forward to seeing you!",
      "timestamp": "2025-11-22T15:03:01Z"
    }
  ]
}
```

---

## Backend Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Dependencies
├── .env.example           # Environment variables template
├── database.db            # SQLite database (created on first run)
├── app/
│   ├── __init__.py
│   ├── config.py          # Environment config
│   ├── database.py        # SQLite connection & models
│   ├── models.py          # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── slots.py       # /api/slots/* endpoints
│   │   ├── appointments.py # /api/appointments
│   │   ├── messages.py    # /api/messages
│   │   ├── campaigns.py   # /api/campaigns/*
│   │   └── webhooks.py    # /webhooks/twilio
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_service.py    # Customer evaluation, message generation, sentiment analysis
│   │   ├── twilio_service.py    # WhatsApp sending/receiving
│   │   ├── scheduler_service.py # APScheduler setup
│   │   └── campaign_service.py  # Campaign orchestration logic
│   └── utils/
│       ├── __init__.py
│       └── helpers.py     # Utility functions
└── tests/                 # Optional for demo
```

---

## Key Services Implementation

### `openai_service.py` - AI Functions (EXPANDED)

```python
async def evaluate_customers_with_openai(candidates):
    """Rank customers for outreach"""
    
    system_prompt = """You evaluate customers for slot-filling campaigns.
    Score each customer 0-10 based on:
 - Message sentiment (avoid recent complaints)
 - Booking history (prefer repeat customers)
 - Responsiveness
    Return JSON: [{"customer_id": 123, "score": 8, "reason": "..."}]
    """
    
    customer_data = [format_customer_for_eval(c) for c in candidates]
    
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(customer_data)}
        ],
        response_format={"type": "json_object"}
    )
    
    scores = json.loads(response.choices[0].message.content)
    return sort_by_score(scores)


async def generate_personalized_outreach_message(customer, campaign):
    """
    Generate personalized message for slot offer
    Uses customer name, chat history, and business owner's custom context
    """
    
    # Get recent message history
    recent_messages = get_recent_messages(customer.id, limit=5)
    message_history_text = format_messages_for_llm(recent_messages)
    
    # Get customer's future appointment
    future_apt = get_future_appointment(customer.id)
    
    system_prompt = """You are a friendly small business owner reaching out to a customer 
    via WhatsApp to offer them an earlier appointment slot. 
    
    Guidelines:
 - Use their first name
 - Keep it casual and warm (this is WhatsApp)
 - Reference their existing appointment briefly
 - Mention the discount as an incentive
 - If there's chat history, reference it naturally
 - If business owner provided context, weave it in naturally
 - Keep it under 3 sentences
 - Use emojis sparingly (max 1-2)
 - End with a clear question/call to action
    """
    
    user_prompt = f"""
    Customer name: {customer.name}
    Their current appointment: {future_apt.service_type} on {future_apt.scheduled_time}
    
    New slot being offered: {campaign.cancelled_slot_time}
    Discount: {campaign.discount_percentage}%
    
    Recent chat history with this customer:
    {message_history_text if message_history_text else "No previous messages"}
    
    Business owner's context: {campaign.custom_context if campaign.custom_context else "Regular slot fill"}
    
    Generate a personalized WhatsApp message offering them the earlier slot.
    """
    
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content


async def analyze_customer_response(message_text):
    """Determine if customer accepted, declined, or unclear"""
    
    system_prompt = """Analyze customer WhatsApp response to a reschedule offer.
    Return JSON: {"intent": "accept|decline|unclear", "confidence": 0.0-1.0}
    """
    
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_text}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


async def generate_response_message(customer, campaign, intent, customer_message):
    """
    Generate personalized response based on customer's reply
    """
    
    recent_messages = get_recent_messages(customer.id, limit=10)
    conversation_context = format_messages_for_llm(recent_messages)
    
    if intent == "accept":
        system_prompt = """Generate a warm confirmation message for a customer who accepted 
        the slot offer. Be enthusiastic, confirm details, and maintain the friendly tone."""
        
        user_prompt = f"""
        Customer {customer.name} just accepted your offer for {campaign.cancelled_slot_time}.
        Their message: "{customer_message}"
        Discount: {campaign.discount_percentage}%
        
        Generate a confirmation response (2 sentences max).
        """
    
    elif intent == "decline":
        system_prompt = """Generate a friendly acknowledgment for a customer who declined.
        Be understanding, confirm their original appointment stands."""
        
        user_prompt = f"""
        Customer {customer.name} declined your reschedule offer.
        Their message: "{customer_message}"
        
        Generate a friendly acknowledgment (1-2 sentences).
        """
    
    else:  # unclear
        system_prompt = """Generate a clarifying message to help customer understand 
        the offer and respond clearly."""
        
        user_prompt = f"""
        Customer {customer.name} sent an unclear response to your slot offer.
        Their message: "{customer_message}"
        Slot offered: {campaign.cancelled_slot_time}
        Discount: {campaign.discount_percentage}%
        
        Generate a clarifying message asking for YES or NO (2 sentences max).
        """
    
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content


async def generate_slot_filled_notification(customer, winner_name):
    """Generate personalized 'slot filled' message for customers who didn't get it"""
    
    system_prompt = """Generate a polite notification that the slot was filled by someone else.
    Confirm their original appointment still stands. Keep it brief and friendly."""
    
    user_prompt = f"""
    Customer {customer.name} was offered a slot but someone else accepted first.
    Generate a brief notification (1-2 sentences).
    """
    
    response = await openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content
```

---

### `campaign_service.py` - Core Functions (UPDATED)

```python
async def trigger_slot_fill(slot_time, service_type, discount, wait_time, custom_context=None):
    """Main entry point"""
    # 1. Create campaign
    campaign = create_campaign(slot_time, service_type, discount, wait_time, custom_context)
    
    # 2. Get and evaluate candidates
    candidates = get_future_appointment_customers(service_type)
    ranked = await evaluate_customers_with_openai(candidates)
    
    # 3. Send to first batch with personalized messages
    await send_batch(campaign.id, ranked[:3], batch_num=1)
    
    # 4. Schedule next batch
    schedule_next_batch(campaign.id, wait_time)
    
    return campaign


async def send_batch(campaign_id, customers, batch_num):
    """Send personalized WhatsApp messages to a batch of customers"""
    campaign = get_campaign(campaign_id)
    
    for customer in customers:
        # Generate personalized message for THIS customer
        message = await generate_personalized_outreach_message(customer, campaign)
        
        # Send via WhatsApp
        await send_whatsapp(customer.phone, message)
        
        # Record outreach with the personalized message
        create_outreach(
            campaign_id=campaign_id,
            customer_id=customer.id,
            batch_number=batch_num,
            message_sent=message,
            status='sent'
        )


async def handle_customer_acceptance(customer_id, campaign_id, customer_message):
    """Called immediately from webhook when customer accepts"""
    
    campaign = get_campaign(campaign_id)
    customer = get_customer(customer_id)
    
    # Race condition check
    if campaign.status != 'active':
        await send_whatsapp(
            customer.phone,
            "Sorry, this slot was just filled by another customer!"
        )
        return
    
    # ATOMIC: Mark campaign as filled
    with db_transaction():
        update_campaign(campaign_id, status='filled', filled_by_customer_id=customer_id)
        update_outreach(campaign_id, customer_id, status='accepted')
        
        # Update appointment
        old_appointment = get_future_appointment(customer_id)
        old_appointment.scheduled_time = campaign.cancelled_slot_time
    
    # Generate and send personalized confirmation
    confirmation = await generate_response_message(
        customer, campaign, 'accept', customer_message
    )
    await send_whatsapp(customer.phone, confirmation)
    
    # Notify all others with personalized messages
    other_outreach = get_active_outreach_except(campaign_id, customer_id)
    for outreach in other_outreach:
        other_customer = get_customer(outreach.customer_id)
        notification = await generate_slot_filled_notification(
            other_customer, customer.name
        )
        await send_whatsapp(other_customer.phone, notification)
        update_outreach_status(outreach.id, 'notified_filled')
    
    # Cancel scheduled jobs
    cancel_campaign_jobs(campaign_id)
```

---

## Example Message Generation

### Scenario 1: First outreach to loyal customer

**Input:**

- Customer: Sarah Johnson
- Chat history: "Thanks for the great cut last time!" (3 weeks ago)
- Custom context: "One of my regulars cancelled - lunch break slot"
- Discount: 10%

**Generated message:**

> "Hi Sarah! Hope you're well 😊 One of my regulars just cancelled their lunch slot tomorrow at 2pm - I remembered you have an appointment next Tuesday. Would you like to come in earlier and save 10%?"

### Scenario 2: Customer accepts

**Input:**

- Customer message: "Yes please! That works perfect"

**Generated response:**

> "Awesome Sarah! You're all set for tomorrow at 2pm with 10% off. Looking forward to seeing you! 🎉"

### Scenario 3: Notifying others

**Input:**

- Customer: Mike Chen

**Generated notification:**

> "Hi Mike! Thanks for your interest - that slot just got filled. Your appointment next Thursday at 3pm is still confirmed! 👍"

---

## Updated Campaign State Machine

```
TRIGGER (with custom_context)
  ↓
EVALUATE_CUSTOMERS (OpenAI)
  ↓
GENERATE_PERSONALIZED_MESSAGES (OpenAI for each)
  ↓
SEND_BATCH_1 (3 customers, each with unique message)
  ↓
SCHEDULE_NEXT_BATCH (+wait_time minutes)
  ↓
┌─────────────── WEBHOOK RECEIVED ─────────────────┐
│                                                   │
│  ANALYZE_INTENT (OpenAI)                        │
│  GENERATE_RESPONSE (OpenAI)                     │
│                                                   │
│  ┌────────────┬────────────────┬──────────────┐ │
│  ↓            ↓                ↓              ↓ │
│ ACCEPT     DECLINE         UNCLEAR       (silence)
│  ↓            ↓                ↓              ↓
│ FILL SLOT  Personalized   Personalized  Wait for
│  ↓         acknowledgment  clarification next batch
│ Personalized   ↓                ↓              ↓
│ confirmations  Campaign    Wait for      SEND_BATCH_2
│  ↓         continues      response      (personalized)
│ END                           ↓              ↓
│                          (loop back)    (previous batch
│                                          still active)
└───────────────────────────────────────────────────┘
```

---

## Environment Variables (.env)

```
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
DATABASE_URL=sqlite:///./database.db
LOG_LEVEL=INFO
```

---

## Minimal Viable Demo Flow

1. Seed DB with customers who have message history
2. Call `POST /api/slots/fill`:

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `cancelled_slot_time`: tomorrow 2pm
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `discount_percentage`: 10
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `wait_time_minutes`: 1
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                - `custom_context`: "My lunch slot opened up last minute!"

3. Backend generates 3 unique personalized messages, sends via WhatsApp
4. Judge texts back "Yes that works!"
5. **IMMEDIATE personalized response:** "Perfect Sarah! See you tomorrow at 2pm with 10% off!"
6. Other 2 customers **IMMEDIATELY** get personalized "slot filled" messages
7. Lovable dashboard shows all personalized messages in real-time
8. Total demo time: 2 minutes

**Demo impresses with: Natural conversation, personalization, AI orchestration, immediate responses**

---

## Critical Implementation Notes

1. **LLM for ALL Messages:** Every outbound message is generated by OpenAI for natural, personalized communication
2. **Context Matters:** Pass customer name, chat history, and business context to every LLM call
3. **Race Condition Handling:** Use DB transactions when marking campaign as filled
4. **Immediate Webhooks:** Generate and send LLM responses in <5 seconds
5. **Message Storage:** Store sent messages in `campaign_outreach.message_sent` for audit trail
6. **Cost Optimization:** Use gpt-4o-mini for message generation (faster + cheaper than gpt-4)

---

## Future Enhancements (Out of Scope)

- Multi-language message generation
- A/B test different message styles
- Learn from customer response patterns
- Voice tone customization per business
- Image/GIF support in messages

### To-dos

- [ ] Initialize FastAPI project, virtual env, install dependencies, create folder structure
- [ ] Define SQLAlchemy models and create database initialization with seed data
- [ ] Implement Twilio WhatsApp send/receive with webhook handler and signature verification
- [ ] Build OpenAI customer evaluation service with proper prompting for ranking candidates
- [ ] Implement campaign orchestration with batch sending and cascade logic
- [ ] Integrate APScheduler for 30-minute response checking and automatic follow-ups
- [ ] Build all 5 REST endpoints with proper error handling and validation
- [ ] Test complete flow with seed data and verify autonomous operation