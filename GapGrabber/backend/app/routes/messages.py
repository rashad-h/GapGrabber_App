from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from collections import defaultdict
from app.database import get_db, Message, Customer, CampaignOutreach
from app.models import MessagesResponse, MessagesByCustomerResponse, MessageResponse, CustomerMessages, CustomerInfo
from sqlalchemy import and_

router = APIRouter(prefix="/api/messages", tags=["messages"])


@router.get("", response_model=MessagesByCustomerResponse)
async def get_messages(
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    campaign_id: Optional[int] = Query(None, description="Filter by campaign"),
    db: Session = Depends(get_db)
):
    """Get conversation history organized by customer"""
    query = db.query(Message)
    
    if customer_id:
        query = query.filter(Message.customer_id == customer_id)
    
    if campaign_id:
        # Get customer IDs from campaign outreach
        outreach_customers = db.query(CampaignOutreach.customer_id).filter(
            CampaignOutreach.campaign_id == campaign_id
        ).all()
        customer_ids = [c[0] for c in outreach_customers]
        query = query.filter(Message.customer_id.in_(customer_ids))
    
    messages = query.order_by(Message.timestamp.asc()).limit(100).all()
    
    # Group messages by customer
    customer_messages_map = defaultdict(list)
    customer_info_map = {}
    
    for msg in messages:
        if msg.customer_id not in customer_info_map:
            customer = db.query(Customer).filter(Customer.id == msg.customer_id).first()
            if customer:
                customer_info_map[msg.customer_id] = CustomerInfo(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone_number
                )
        
        if msg.customer_id in customer_info_map:
            customer_messages_map[msg.customer_id].append(MessageResponse(
                id=msg.id,
                customer=customer_info_map[msg.customer_id],
                direction=msg.direction,
                content=msg.content,
                timestamp=msg.timestamp
            ))
    
    # Build response grouped by customer
    result = []
    for customer_id, msgs in customer_messages_map.items():
        result.append(CustomerMessages(
            customer=customer_info_map[customer_id],
            messages=msgs  # Already in chronological order (ascending)
        ))
    
    # Sort by most recent message timestamp (descending)
    result.sort(key=lambda x: x.messages[-1].timestamp if x.messages else None, reverse=True)
    
    return MessagesByCustomerResponse(messages_by_customer=result)

