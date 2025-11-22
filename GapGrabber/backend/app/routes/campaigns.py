from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db, SlotFillCampaign, CampaignOutreach, Customer
from app.models import CampaignResponse, CampaignsResponse, CampaignSummary, OutreachAttempt, CustomerInfo
from sqlalchemy import func

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("", response_model=CampaignsResponse)
async def get_all_campaigns(
    status: Optional[str] = Query(None, description="Filter by status (active, filled, expired)"),
    db: Session = Depends(get_db)
):
    """Get all campaigns"""
    query = db.query(SlotFillCampaign)
    
    if status:
        query = query.filter(SlotFillCampaign.status == status)
    
    campaigns = query.order_by(SlotFillCampaign.created_at.desc()).all()
    
    result = []
    for campaign in campaigns:
        # Get outreach count
        outreach_count = db.query(CampaignOutreach).filter(
            CampaignOutreach.campaign_id == campaign.id
        ).count()
        
        # Get current batch number
        max_batch = db.query(func.max(CampaignOutreach.batch_number)).filter(
            CampaignOutreach.campaign_id == campaign.id
        ).scalar() or 0
        
        result.append(CampaignSummary(
            id=campaign.id,
            status=campaign.status,
            cancelled_slot_time=campaign.cancelled_slot_time,
            service_type=campaign.service_type,
            discount_percentage=campaign.discount_percentage,
            wait_time_minutes=campaign.wait_time_minutes,
            current_batch=max_batch,
            total_contacted=outreach_count,
            created_at=campaign.created_at
        ))
    
    return CampaignsResponse(campaigns=result)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get campaign status and outreach details"""
    campaign = db.query(SlotFillCampaign).filter(
        SlotFillCampaign.id == campaign_id
    ).first()
    
    if not campaign:
        # Check if any campaigns exist to provide helpful error message
        total_campaigns = db.query(SlotFillCampaign).count()
        if total_campaigns == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"Campaign {campaign_id} not found. No campaigns exist yet. Create a campaign first by canceling an appointment."
            )
        else:
            # Get available campaign IDs for helpful error
            available_ids = [c.id for c in db.query(SlotFillCampaign.id).all()]
            raise HTTPException(
                status_code=404, 
                detail=f"Campaign {campaign_id} not found. Available campaign IDs: {available_ids}"
            )
    
    # Get outreach attempts
    outreach_list = db.query(CampaignOutreach).filter(
        CampaignOutreach.campaign_id == campaign_id
    ).order_by(CampaignOutreach.batch_number, CampaignOutreach.sent_at).all()
    
    # Get current batch number
    max_batch = db.query(func.max(CampaignOutreach.batch_number)).filter(
        CampaignOutreach.campaign_id == campaign_id
    ).scalar() or 0
    
    outreach_attempts = []
    for outreach in outreach_list:
        customer = db.query(Customer).filter(
            Customer.id == outreach.customer_id
        ).first()
        if customer:
            outreach_attempts.append(OutreachAttempt(
                customer=CustomerInfo(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone_number
                ),
                status=outreach.status,
                batch_number=outreach.batch_number,
                message_sent=outreach.message_sent,
                sent_at=outreach.sent_at,
                responded_at=outreach.responded_at
            ))
    
    return CampaignResponse(
        id=campaign.id,
        status=campaign.status,
        cancelled_slot_time=campaign.cancelled_slot_time,
        discount_percentage=campaign.discount_percentage,
        wait_time_minutes=campaign.wait_time_minutes,
        custom_context=campaign.custom_context,
        current_batch=max_batch,
        total_contacted=len(outreach_attempts),
        outreach_attempts=outreach_attempts
    )

