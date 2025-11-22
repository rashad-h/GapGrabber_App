from datetime import datetime, timedelta
from typing import List
from app.database import Message, Appointment


def format_messages_for_llm(messages: List[Message]) -> str:
    """Format message history for LLM context"""
    if not messages:
        return "No previous messages"
    
    formatted = []
    for msg in messages[-5:]:  # Last 5 messages
        direction = "Customer" if msg.direction == "inbound" else "Business"
        formatted.append(f"{direction}: {msg.content}")
    
    return "\n".join(formatted)


def format_customer_for_eval(customer, appointments: List[Appointment], messages: List[Message]) -> dict:
    """Format customer data for OpenAI evaluation"""
    booking_count = len([a for a in appointments if a.status == "completed"])
    recent_messages = messages[-3:] if messages else []
    
    return {
        "customer_id": customer.id,
        "name": customer.name,
        "booking_count": booking_count,
        "recent_messages": [{"direction": m.direction, "content": m.content[:100]} for m in recent_messages]
    }

