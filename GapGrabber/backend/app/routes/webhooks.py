from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db, Customer, Message, CampaignOutreach, SlotFillCampaign
from app.services.twilio_service import verify_twilio_request, send_whatsapp_message
from app.services.openai_service import analyze_customer_response
from app.services.campaign_service import (
    handle_customer_acceptance,
    handle_customer_decline,
    handle_customer_unclear
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/twilio")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...),
    db: Session = Depends(get_db)
):
    """Receive incoming WhatsApp messages from Twilio"""
    
    # Verify Twilio signature (optional for development, required for production)
    # signature = request.headers.get("X-Twilio-Signature")
    # if not verify_twilio_request(str(request.url), dict(request.form), signature):
    #     raise HTTPException(status_code=403, detail="Invalid signature")
    
    try:
        # Extract phone number (remove whatsapp: prefix if present)
        phone_number = From.replace("whatsapp:", "")
        
        # Find the most recent active campaign (link to first message sent)
        # Since all messages go to test number, we find the most recent campaign
        logger.info(f"🔍 Finding most recent active campaign...")
        active_outreach = db.query(CampaignOutreach).join(SlotFillCampaign).filter(
            CampaignOutreach.status == 'sent',
            SlotFillCampaign.status == 'active'
        ).order_by(CampaignOutreach.sent_at.desc()).first()
        
        if not active_outreach:
            # No active campaign, just acknowledge
            logger.info(f"Message from {phone_number} but no active campaign")
            return {"status": "ok"}
        
        campaign_id = active_outreach.campaign_id
        
        # Use the customer from the FIRST outreach in this campaign (the first message sent)
        # This is the customer we're processing the response for
        first_outreach = db.query(CampaignOutreach).filter(
            CampaignOutreach.campaign_id == campaign_id,
            CampaignOutreach.status == 'sent'
        ).order_by(CampaignOutreach.sent_at.asc()).first()
        
        if not first_outreach:
            logger.warning(f"⚠️  Could not find first outreach for campaign {campaign_id}")
            return {"status": "ok"}
        
        actual_customer_id = first_outreach.customer_id
        actual_customer = db.query(Customer).filter(Customer.id == actual_customer_id).first()
        
        if not actual_customer:
            logger.warning(f"⚠️  Could not find customer {actual_customer_id} for outreach {first_outreach.id}")
            return {"status": "ok"}
        
        customer = actual_customer  # Use the actual customer for processing
        logger.info(f"📋 Processing response for campaign {campaign_id}, customer: {actual_customer.name} (from first outreach)")
        
        # Save incoming message linked to the actual customer
        inbound_message = Message(
            customer_id=customer.id,
            direction='inbound',
            content=Body,
            twilio_sid=MessageSid
        )
        db.add(inbound_message)
        db.commit()
        
        # Analyze customer response with OpenAI
        try:
            analysis = await analyze_customer_response(Body)
            intent = analysis.get("intent", "unclear")
            confidence = analysis.get("confidence", 0.0)
            
            logger.info(f"Customer {customer.id} response: intent={intent}, confidence={confidence}")
            
            # Handle based on intent
            if intent == "accept" and confidence > 0.7:
                await handle_customer_acceptance(db, customer.id, campaign_id, Body)
            elif intent == "decline" and confidence > 0.7:
                await handle_customer_decline(db, customer.id, campaign_id, Body)
            else:
                await handle_customer_unclear(db, customer.id, campaign_id, Body)
                
        except Exception as e:
            logger.error(f"Error processing customer response: {str(e)}")
            # Still return 200 to Twilio
            return {"status": "ok"}
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        # Always return 200 to Twilio to prevent retries
        return {"status": "ok"}

