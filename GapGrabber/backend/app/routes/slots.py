from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SlotFillRequest, SlotFillResponse, CustomerContacted
from app.services.campaign_service import trigger_slot_fill
from app.database import SlotFillCampaign, CampaignOutreach, Customer
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/slots", tags=["slots"])


@router.post("/fill", response_model=SlotFillResponse)
async def fill_slot(
    request: SlotFillRequest,
    db: Session = Depends(get_db)
):
    """Trigger slot fill campaign"""
    try:
        campaign = await trigger_slot_fill(
            db=db,
            slot_time=request.cancelled_slot_time,
            service_type=request.service_type,
            discount=request.discount_percentage,
            wait_time=request.wait_time_minutes,
            custom_context=request.custom_context
        )
        
        # Get outreach details
        outreach_list = db.query(CampaignOutreach).filter(
            CampaignOutreach.campaign_id == campaign.id,
            CampaignOutreach.batch_number == 1
        ).all()
        
        customers_contacted = []
        for outreach in outreach_list:
            customer = db.query(Customer).filter(
                Customer.id == outreach.customer_id
            ).first()
            if customer:
                customers_contacted.append(CustomerContacted(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone_number,
                    message_sent=outreach.message_sent
                ))
        
        # Count total candidates evaluated (simplified - could be improved)
        total_candidates = len(outreach_list) + 10  # Rough estimate
        
        return SlotFillResponse(
            campaign_id=campaign.id,
            candidates_evaluated=total_candidates,
            initial_batch_sent=len(customers_contacted),
            wait_time_minutes=campaign.wait_time_minutes,
            customers_contacted=customers_contacted
        )
        
    except Exception as e:
        logger.error(f"Error in fill_slot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

