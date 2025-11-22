from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database import get_db, Appointment, Customer
from app.models import AppointmentsResponse, AppointmentResponse, CustomerInfo
from app.services.campaign_service import trigger_slot_fill
from sqlalchemy import and_
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


class CancelAppointmentRequest(BaseModel):
    discount_percentage: int = 10
    wait_time_minutes: int = 30
    custom_context: Optional[str] = None


@router.get("", response_model=AppointmentsResponse)
async def get_appointments(
    status: Optional[str] = Query(None, description="Filter by status"),
    from_date: Optional[datetime] = Query(None, description="Start date"),
    to_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Get all appointments"""
    query = db.query(Appointment)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if from_date:
        query = query.filter(Appointment.scheduled_time >= from_date)
    
    if to_date:
        query = query.filter(Appointment.scheduled_time <= to_date)
    
    appointments = query.order_by(Appointment.scheduled_time).all()
    
    result = []
    for apt in appointments:
        customer = db.query(Customer).filter(Customer.id == apt.customer_id).first()
        if customer:
            result.append(AppointmentResponse(
                id=apt.id,
                customer=CustomerInfo(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone_number
                ),
                scheduled_time=apt.scheduled_time,
                service_type=apt.service_type,
                status=apt.status
            ))
    
    return AppointmentsResponse(appointments=result)


@router.post("/{appointment_id}/cancel-and-fill")
async def cancel_appointment_and_fill(
    appointment_id: int,
    request: CancelAppointmentRequest,
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment and automatically trigger slot fill campaign.
    This is what the dashboard calls when business owner clicks "Cancel & Fill Slot"
    """
    logger.info(f"🔄 Cancel & Fill triggered for appointment {appointment_id}")
    
    # Get the appointment
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        logger.warning(f"❌ Appointment {appointment_id} not found")
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointment.status != 'scheduled':
        logger.warning(f"⚠️  Appointment {appointment_id} is already {appointment.status}")
        raise HTTPException(
            status_code=400, 
            detail=f"Appointment is already {appointment.status}, cannot cancel"
        )
    
    customer = db.query(Customer).filter(Customer.id == appointment.customer_id).first()
    logger.info(f"📅 Cancelling appointment: {customer.name if customer else 'Unknown'} - {appointment.service_type} at {appointment.scheduled_time}")
    
    # Mark appointment as cancelled
    appointment.status = 'cancelled'
    db.commit()
    logger.info(f"✅ Appointment {appointment_id} marked as cancelled")
    
    # Trigger slot fill campaign
    try:
        logger.info(f"🚀 Triggering slot fill campaign...")
        campaign = await trigger_slot_fill(
            db=db,
            slot_time=appointment.scheduled_time,
            service_type=appointment.service_type,
            discount=request.discount_percentage,
            wait_time=request.wait_time_minutes,
            custom_context=request.custom_context
        )
        logger.info(f"✅ Campaign {campaign.id} triggered successfully")
        
        # Get outreach details for response
        from app.database import CampaignOutreach
        outreach_list = db.query(CampaignOutreach).filter(
            CampaignOutreach.campaign_id == campaign.id,
            CampaignOutreach.batch_number == 1
        ).all()
        
        from app.models import CustomerContacted, SlotFillResponse
        customers_contacted = []
        for outreach in outreach_list:
            customer = db.query(Customer).filter(Customer.id == outreach.customer_id).first()
            if customer:
                customers_contacted.append(CustomerContacted(
                    id=customer.id,
                    name=customer.name,
                    phone=customer.phone_number,
                    message_sent=outreach.message_sent
                ))
        
        total_candidates = len(outreach_list) + 10  # Rough estimate
        
        return SlotFillResponse(
            campaign_id=campaign.id,
            candidates_evaluated=total_candidates,
            initial_batch_sent=len(customers_contacted),
            wait_time_minutes=campaign.wait_time_minutes,
            customers_contacted=customers_contacted
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to trigger campaign: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Rollback appointment cancellation if campaign fails
        appointment.status = 'scheduled'
        db.commit()
        logger.info(f"🔄 Rolled back appointment {appointment_id} to scheduled")
        raise HTTPException(status_code=500, detail=f"Failed to trigger campaign: {str(e)}")

