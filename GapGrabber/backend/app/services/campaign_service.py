from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.database import (
    Customer, Appointment, SlotFillCampaign, CampaignOutreach, Message
)
from app.services.openai_service import (
    evaluate_customers_with_openai,
    generate_personalized_outreach_message,
    generate_response_message,
    generate_slot_filled_notification
)
from app.services.twilio_service import send_whatsapp_message
from app.services.scheduler_service import scheduler
import logging

logger = logging.getLogger(__name__)


async def trigger_slot_fill(
    db: Session,
    slot_time: datetime,
    service_type: str,
    discount: int,
    wait_time: int,
    custom_context: Optional[str] = None
) -> SlotFillCampaign:
    """Main entry point for slot fill campaign"""
    
    logger.info(f"🚀 Starting slot fill campaign: {service_type} at {slot_time}, discount={discount}%")
    
    # 1. Create campaign
    campaign = SlotFillCampaign(
        cancelled_slot_time=slot_time,
        service_type=service_type,
        discount_percentage=discount,
        wait_time_minutes=wait_time,
        custom_context=custom_context,
        status='active'
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    logger.info(f"✅ Campaign {campaign.id} created")
    
    # 2. Get candidates (customers with future appointments 7-14 days out)
    # For testing: expand window and be flexible with service type matching
    now = datetime.utcnow()
    future_start = now + timedelta(days=5)  # Expanded from 7 to 5 days
    future_end = now + timedelta(days=21)   # Expanded from 14 to 21 days
    
    # First try exact service type match
    candidates = db.query(Customer).join(Appointment).filter(
        and_(
            Appointment.status == 'scheduled',
            Appointment.scheduled_time >= future_start,
            Appointment.scheduled_time <= future_end,
            Appointment.service_type == service_type
        )
    ).distinct().all()
    
    # If no exact match, try any future appointments (for testing)
    if not candidates:
        logger.info(f"⚠️  No exact matches for {service_type}, trying any future appointments...")
        candidates = db.query(Customer).join(Appointment).filter(
            and_(
                Appointment.status == 'scheduled',
                Appointment.scheduled_time >= future_start,
                Appointment.scheduled_time <= future_end
            )
        ).distinct().limit(5).all()  # Limit to 5 for testing
    
    logger.info(f"📋 Found {len(candidates)} potential candidates for {service_type}")
    
    if not candidates:
        logger.warning(f"⚠️  No candidates found at all, creating test message to test number")
        # Still create campaign but mark as expired
        campaign.status = 'expired'
        db.commit()
        return campaign
    
    if len(candidates) < 3:
        logger.info(f"ℹ️  Only {len(candidates)} candidates found (less than 3), will send to all")
    
    # 3. Get appointments and messages for evaluation
    logger.info("📊 Gathering customer data for evaluation...")
    appointments_map = {}
    messages_map = {}
    
    for customer in candidates:
        appointments_map[customer.id] = db.query(Appointment).filter(
            Appointment.customer_id == customer.id
        ).all()
        messages_map[customer.id] = db.query(Message).filter(
            Message.customer_id == customer.id
        ).order_by(Message.timestamp.desc()).limit(10).all()
    
    # 4. Evaluate customers with OpenAI
    logger.info("🤖 Evaluating customers with OpenAI...")
    ranked_scores = await evaluate_customers_with_openai(
        candidates, appointments_map, messages_map
    )
    logger.info(f"✅ Evaluated {len(ranked_scores)} customers")
    
    # Map scores back to customers
    customer_scores = {score['customer_id']: score for score in ranked_scores}
    sorted_candidates = sorted(
        candidates,
        key=lambda c: customer_scores.get(c.id, {}).get('score', 0),
        reverse=True
    )
    
    # Log top candidates (send to top 3, or all if less than 3)
    # For testing: select 3 customers for DB records, but only send 1 WhatsApp message
    batch_size = min(3, len(sorted_candidates))  # Select top 3 for database
    top_candidates = sorted_candidates[:batch_size]
    logger.info(f"🏆 Top {batch_size} candidate(s) selected (will create {batch_size} DB records, send 1 WhatsApp):")
    for i, c in enumerate(top_candidates, 1):
        score = customer_scores.get(c.id, {}).get('score', 0)
        logger.info(f"   {i}. {c.name} (score: {score})")
    
    # 5. Send to first batch (3 customers in DB, 1 WhatsApp message)
    logger.info(f"📤 Sending messages to first batch of {len(top_candidates)} customer(s) (1 WhatsApp, {len(top_candidates)} DB records)...")
    await send_batch(db, campaign.id, top_candidates, batch_num=1)
    logger.info(f"✅ First batch sent for campaign {campaign.id}")
    
    # 6. Schedule next batch
    logger.info(f"⏰ Scheduling next batch in {wait_time} minutes...")
    schedule_next_batch(campaign.id, wait_time)
    
    logger.info(f"🎉 Campaign {campaign.id} initiated successfully!")
    return campaign


async def send_batch(
    db: Session,
    campaign_id: int,
    customers: List[Customer],
    batch_num: int
):
    """Send personalized WhatsApp messages to a batch of customers"""
    logger.info(f"📨 Sending batch {batch_num} for campaign {campaign_id} to {len(customers)} customers")
    
    campaign = db.query(SlotFillCampaign).filter(
        SlotFillCampaign.id == campaign_id
    ).first()
    
    if not campaign or campaign.status != 'active':
        logger.warning(f"⚠️  Campaign {campaign_id} is not active, skipping batch {batch_num}")
        return
    
    # Generate messages for all customers and create outreach records
    # But only send ONE WhatsApp message (to test number) for demo purposes
    from app.config import settings
    test_number = settings.test_whatsapp_number.replace('+', '')
    whatsapp_sent = False
    twilio_sid = None
    
    for idx, customer in enumerate(customers):
        try:
            # Get customer's future appointment (try matching service type first, then any)
            future_apt = db.query(Appointment).filter(
                and_(
                    Appointment.customer_id == customer.id,
                    Appointment.status == 'scheduled',
                    Appointment.service_type == campaign.service_type
                )
            ).order_by(Appointment.scheduled_time).first()
            
            # If no matching service type, get any future appointment (for testing)
            if not future_apt:
                logger.info(f"ℹ️  No {campaign.service_type} appointment for {customer.name}, trying any future appointment...")
                future_apt = db.query(Appointment).filter(
                    and_(
                        Appointment.customer_id == customer.id,
                        Appointment.status == 'scheduled'
                    )
                ).order_by(Appointment.scheduled_time).first()
            
            if not future_apt:
                logger.warning(f"⚠️  Customer {customer.name} ({customer.id}) has no future scheduled appointment, skipping")
                continue
            
            logger.info(f"📅 Found future appointment for {customer.name}: {future_apt.service_type} on {future_apt.scheduled_time}")
            
            # Get recent messages
            recent_messages = db.query(Message).filter(
                Message.customer_id == customer.id
            ).order_by(Message.timestamp.desc()).limit(5).all()
            
            # Generate personalized message for this customer
            message_text = await generate_personalized_outreach_message(
                customer, campaign, future_apt, recent_messages
            )
            
            # Send WhatsApp ONLY ONCE (for first customer in batch)
            if not whatsapp_sent:
                logger.info(f"📤 TEST MODE: Sending ONE WhatsApp message to test number {test_number} (representing {len(customers)} customers)...")
                try:
                    twilio_sid = await send_whatsapp_message(test_number, message_text)
                    logger.info(f"✅ WhatsApp sent to test number! SID: {twilio_sid}")
                    whatsapp_sent = True
                except Exception as whatsapp_error:
                    logger.error(f"❌ WhatsApp send failed: {str(whatsapp_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise  # Re-raise to be caught by outer exception handler
            
            # Save message to DB for THIS customer (even though WhatsApp was only sent once)
            outbound_message = Message(
                customer_id=customer.id,
                direction='outbound',
                content=message_text,
                twilio_sid=twilio_sid if whatsapp_sent else f"TEST-{customer.id}-{batch_num}"  # Use same SID or generate test SID
            )
            db.add(outbound_message)
            
            # Record outreach for THIS customer
            outreach = CampaignOutreach(
                campaign_id=campaign_id,
                customer_id=customer.id,
                batch_number=batch_num,
                message_sent=message_text,
                status='sent'
            )
            db.add(outreach)
            
            logger.info(f"✅ Created outreach record for {customer.name} (batch {batch_num})")
            logger.info(f"   Message: {message_text[:100]}...")
            
        except Exception as e:
            logger.error(f"❌ Error processing {customer.name} ({customer.phone_number}): {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            db.rollback()
            continue
    
    # Commit all outreach records at once
    try:
        db.commit()
        logger.info(f"✅ Batch {batch_num} completed: {len(customers)} outreach records created, 1 WhatsApp message sent")
    except Exception as e:
        logger.error(f"❌ Error committing batch {batch_num}: {str(e)}")
        db.rollback()
        raise
    
    logger.info(f"✅ Batch {batch_num} completed for campaign {campaign_id}")


def schedule_next_batch(campaign_id: int, wait_minutes: int):
    """Schedule sending to next batch after wait time"""
    run_date = datetime.utcnow() + timedelta(minutes=wait_minutes)
    
    # Import here to avoid circular import at module level
    import app.services.campaign_service as campaign_module
    
    scheduler.add_job(
        campaign_module.send_next_batch_job,
        'date',
        run_date=run_date,
        args=[campaign_id],
        id=f'campaign_{campaign_id}_next_batch',
        replace_existing=True
    )
    
    logger.info(f"Scheduled next batch for campaign {campaign_id} at {run_date}")


async def send_next_batch_job(campaign_id: int):
    """Scheduled job to send to next batch"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        campaign = db.query(SlotFillCampaign).filter(
            SlotFillCampaign.id == campaign_id
        ).first()
        
        if not campaign or campaign.status != 'active':
            logger.info(f"Campaign {campaign_id} is no longer active, skipping batch")
            return
        
        # Get already contacted customers
        contacted = db.query(CampaignOutreach.customer_id).filter(
            CampaignOutreach.campaign_id == campaign_id
        ).all()
        contacted_ids = [c[0] for c in contacted]
        
        # Get remaining candidates
        now = datetime.utcnow()
        future_start = now + timedelta(days=7)
        future_end = now + timedelta(days=14)
        
        remaining = db.query(Customer).join(Appointment).filter(
            and_(
                Appointment.status == 'scheduled',
                Appointment.scheduled_time >= future_start,
                Appointment.scheduled_time <= future_end,
                Appointment.service_type == campaign.service_type,
                ~Customer.id.in_(contacted_ids)
            )
        ).distinct().limit(3).all()
        
        if not remaining:
            logger.info(f"No more candidates for campaign {campaign_id}, marking as expired")
            campaign.status = 'expired'
            db.commit()
            return
        
        # Get current batch number
        max_batch = db.query(CampaignOutreach.batch_number).filter(
            CampaignOutreach.campaign_id == campaign_id
        ).order_by(CampaignOutreach.batch_number.desc()).first()
        
        next_batch = (max_batch[0] if max_batch else 0) + 1
        
        # Send to next batch
        await send_batch(db, campaign_id, remaining, next_batch)
        
        # Schedule next cascade
        schedule_next_batch(campaign_id, campaign.wait_time_minutes)
        
    except Exception as e:
        logger.error(f"Error in send_next_batch_job for campaign {campaign_id}: {str(e)}")
        db.rollback()
    finally:
        db.close()


async def handle_customer_acceptance(
    db: Session,
    customer_id: int,
    campaign_id: int,
    customer_message: str
):
    """Called immediately from webhook when customer accepts"""
    
    campaign = db.query(SlotFillCampaign).filter(
        SlotFillCampaign.id == campaign_id
    ).first()
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    
    if not campaign or not customer:
        return
    
    # Race condition check
    if campaign.status != 'active':
        from app.config import settings
        test_number = settings.test_whatsapp_number.replace('+', '')
        await send_whatsapp_message(
            test_number,
            "Sorry, this slot was just filled by another customer!"
        )
        return
    
    try:
        # ATOMIC: Mark campaign as filled
        campaign.status = 'filled'
        campaign.filled_by_customer_id = customer_id
        
        # Update outreach status
        outreach = db.query(CampaignOutreach).filter(
            and_(
                CampaignOutreach.campaign_id == campaign_id,
                CampaignOutreach.customer_id == customer_id
            )
        ).first()
        
        if outreach:
            outreach.status = 'accepted'
            outreach.responded_at = datetime.utcnow()
        
        # Update appointment
        old_appointment = db.query(Appointment).filter(
            and_(
                Appointment.customer_id == customer_id,
                Appointment.status == 'scheduled'
            )
        ).order_by(Appointment.scheduled_time).first()
        
        if old_appointment:
            old_appointment.scheduled_time = campaign.cancelled_slot_time
        
        db.commit()
        
        # Generate and send personalized confirmation
        confirmation = await generate_response_message(
            customer, campaign, 'accept', customer_message
        )
        # TEST MODE: Always send to test number
        from app.config import settings
        test_number = settings.test_whatsapp_number.replace('+', '')
        await send_whatsapp_message(test_number, confirmation)
        
        # Save confirmation message
        confirm_msg = Message(
            customer_id=customer_id,
            direction='outbound',
            content=confirmation
        )
        db.add(confirm_msg)
        db.commit()
        
        # Notify all others with personalized messages
        # NOTE: Don't send WhatsApp (we only have one test number), but save to DB
        other_outreach = db.query(CampaignOutreach).filter(
            and_(
                CampaignOutreach.campaign_id == campaign_id,
                CampaignOutreach.customer_id != customer_id,
                CampaignOutreach.status == 'sent'
            )
        ).all()
        
        for outreach in other_outreach:
            other_customer = db.query(Customer).filter(
                Customer.id == outreach.customer_id
            ).first()
            
            if other_customer:
                notification = await generate_slot_filled_notification(
                    other_customer, customer.name
                )
                
                # TEST MODE: Don't send WhatsApp (only one test number), but save to DB
                logger.info(f"📝 Saving 'slot filled' notification for {other_customer.name} to database (not sending WhatsApp)")
                
                outreach.status = 'notified_filled'
                
                # Save notification message to database (but don't send WhatsApp)
                notify_msg = Message(
                    customer_id=other_customer.id,
                    direction='outbound',
                    content=notification,
                    twilio_sid=f"DB-ONLY-{outreach.id}"  # Mark as DB-only
                )
                db.add(notify_msg)
        
        # Commit all notification messages
        try:
            db.commit()
            logger.info(f"✅ Saved {len(other_outreach)} notification messages for other customers")
        except Exception as e:
            logger.error(f"❌ Error committing notification messages: {str(e)}")
            db.rollback()
            raise
        
        # Cancel scheduled jobs
        try:
            scheduler.remove_job(f'campaign_{campaign_id}_next_batch')
        except:
            pass
        
        logger.info(f"Campaign {campaign_id} filled by customer {customer_id}")
        
    except Exception as e:
        logger.error(f"Error handling acceptance: {str(e)}")
        db.rollback()
        raise


async def handle_customer_decline(
    db: Session,
    customer_id: int,
    campaign_id: int,
    customer_message: str
):
    """Called immediately from webhook when customer declines"""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    campaign = db.query(SlotFillCampaign).filter(
        SlotFillCampaign.id == campaign_id
    ).first()
    
    if not customer or not campaign:
        return
    
    try:
        # Update outreach status
        outreach = db.query(CampaignOutreach).filter(
            and_(
                CampaignOutreach.campaign_id == campaign_id,
                CampaignOutreach.customer_id == customer_id
            )
        ).first()
        
        if outreach:
            outreach.status = 'declined'
            outreach.responded_at = datetime.utcnow()
        
        db.commit()
        
        # Generate and send personalized acknowledgment
        acknowledgment = await generate_response_message(
            customer, campaign, 'decline', customer_message
        )
        # TEST MODE: Always send to test number
        from app.config import settings
        test_number = settings.test_whatsapp_number.replace('+', '')
        await send_whatsapp_message(test_number, acknowledgment)
        
        # Save acknowledgment message
        ack_msg = Message(
            customer_id=customer_id,
            direction='outbound',
            content=acknowledgment
        )
        db.add(ack_msg)
        db.commit()
        
        logger.info(f"Customer {customer_id} declined campaign {campaign_id}")
        
    except Exception as e:
        logger.error(f"Error handling decline: {str(e)}")
        db.rollback()
        raise


async def handle_customer_unclear(
    db: Session,
    customer_id: int,
    campaign_id: int,
    customer_message: str
):
    """Called when customer response is unclear"""
    
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    campaign = db.query(SlotFillCampaign).filter(
        SlotFillCampaign.id == campaign_id
    ).first()
    
    if not customer or not campaign:
        return
    
    try:
        # Generate clarification
        clarification = await generate_response_message(
            customer, campaign, 'unclear', customer_message
        )
        # TEST MODE: Always send to test number
        from app.config import settings
        test_number = settings.test_whatsapp_number.replace('+', '')
        await send_whatsapp_message(test_number, clarification)
        
        # Save clarification message
        clar_msg = Message(
            customer_id=customer_id,
            direction='outbound',
            content=clarification
        )
        db.add(clar_msg)
        db.commit()
        
    except Exception as e:
        logger.error(f"Error handling unclear: {str(e)}")
        db.rollback()
        raise

