import json
from openai import AsyncOpenAI
from app.config import settings
from app.database import Customer, SlotFillCampaign, Message, Appointment
from app.utils.helpers import format_messages_for_llm, format_customer_for_eval
from typing import List, Dict

client = AsyncOpenAI(api_key=settings.openai_api_key)


async def evaluate_customers_with_openai(
    candidates: List[Customer],
    appointments_map: Dict[int, List[Appointment]],
    messages_map: Dict[int, List[Message]]
) -> List[Dict]:
    """Rank customers for outreach"""
    
    system_prompt = """You evaluate customers for slot-filling campaigns.
    Score each customer 0-10 based on:
    - Message sentiment (avoid recent complaints)
    - Booking history (prefer repeat customers)
    - Responsiveness
    Return JSON with a "customers" array containing objects with "customer_id", "score" (0-10), and "reason" fields."""
    
    customer_data = [
        format_customer_for_eval(
            c,
            appointments_map.get(c.id, []),
            messages_map.get(c.id, [])
        )
        for c in candidates
    ]
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(customer_data)}
        ],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    customers = result.get("customers", [])
    
    # Sort by score descending
    return sorted(customers, key=lambda x: x.get("score", 0), reverse=True)


async def generate_personalized_outreach_message(
    customer: Customer,
    campaign: SlotFillCampaign,
    future_appointment: Appointment,
    recent_messages: List[Message]
) -> str:
    """Generate personalized message for slot offer"""
    
    message_history_text = format_messages_for_llm(recent_messages)
    
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
    - End with a clear question/call to action"""
    
    user_prompt = f"""
    Customer name: {customer.name}
    Their current appointment: {future_appointment.service_type} on {future_appointment.scheduled_time.strftime('%Y-%m-%d %I:%M %p')}
    
    New slot being offered: {campaign.cancelled_slot_time.strftime('%Y-%m-%d %I:%M %p')}
    Discount: {campaign.discount_percentage}%
    
    Recent chat history with this customer:
    {message_history_text if message_history_text else "No previous messages"}
    
    Business owner's context: {campaign.custom_context if campaign.custom_context else "Regular slot fill"}
    
    Generate a personalized WhatsApp message offering them the earlier slot.
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()


async def analyze_customer_response(message_text: str) -> Dict:
    """Determine if customer accepted, declined, or unclear"""
    
    system_prompt = """Analyze customer WhatsApp response to a reschedule offer.
    Return JSON: {"intent": "accept|decline|unclear", "confidence": 0.0-1.0}"""
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_text}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


async def generate_response_message(
    customer: Customer,
    campaign: SlotFillCampaign,
    intent: str,
    customer_message: str
) -> str:
    """Generate personalized response based on customer's reply"""
    
    if intent == "accept":
        system_prompt = """Generate a warm confirmation message for a customer who accepted 
        the slot offer. Be enthusiastic, confirm details, and maintain the friendly tone."""
        
        user_prompt = f"""
        Customer {customer.name} just accepted your offer for {campaign.cancelled_slot_time.strftime('%Y-%m-%d %I:%M %p')}.
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
        Slot offered: {campaign.cancelled_slot_time.strftime('%Y-%m-%d %I:%M %p')}
        Discount: {campaign.discount_percentage}%
        
        Generate a clarifying message asking for YES or NO (2 sentences max).
        """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()


async def generate_slot_filled_notification(customer: Customer, winner_name: str) -> str:
    """Generate personalized 'slot filled' message for customers who didn't get it"""
    
    system_prompt = """Generate a polite notification that the slot was filled by someone else.
    Confirm their original appointment still stands. Keep it brief and friendly."""
    
    user_prompt = f"""
    Customer {customer.name} was offered a slot but someone else accepted first.
    Generate a brief notification (1-2 sentences).
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

