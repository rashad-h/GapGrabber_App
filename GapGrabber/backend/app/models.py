from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# Request Models
class SlotFillRequest(BaseModel):
    cancelled_slot_time: datetime
    service_type: str
    discount_percentage: int
    wait_time_minutes: int
    custom_context: Optional[str] = None


# Response Models
class CustomerInfo(BaseModel):
    id: int
    name: str
    phone: str
    
    class Config:
        from_attributes = True


class CustomerContacted(BaseModel):
    id: int
    name: str
    phone: str
    message_sent: str


class SlotFillResponse(BaseModel):
    campaign_id: int
    candidates_evaluated: int
    initial_batch_sent: int
    wait_time_minutes: int
    customers_contacted: List[CustomerContacted]


class AppointmentResponse(BaseModel):
    id: int
    customer: CustomerInfo
    scheduled_time: datetime
    service_type: str
    status: str


class AppointmentsResponse(BaseModel):
    appointments: List[AppointmentResponse]


class OutreachAttempt(BaseModel):
    customer: CustomerInfo
    status: str
    batch_number: int
    message_sent: str
    sent_at: datetime
    responded_at: Optional[datetime] = None


class CampaignResponse(BaseModel):
    id: int
    status: str
    cancelled_slot_time: datetime
    discount_percentage: int
    wait_time_minutes: int
    custom_context: Optional[str]
    current_batch: int
    total_contacted: int
    outreach_attempts: List[OutreachAttempt]


class MessageResponse(BaseModel):
    id: int
    customer: CustomerInfo
    direction: str
    content: str
    timestamp: datetime


class MessagesResponse(BaseModel):
    messages: List[MessageResponse]


class CustomerMessages(BaseModel):
    customer: CustomerInfo
    messages: List[MessageResponse]


class MessagesByCustomerResponse(BaseModel):
    messages_by_customer: List[CustomerMessages]


class CampaignSummary(BaseModel):
    id: int
    status: str
    cancelled_slot_time: datetime
    service_type: str
    discount_percentage: int
    wait_time_minutes: int
    current_batch: int
    total_contacted: int
    created_at: datetime


class CampaignsResponse(BaseModel):
    campaigns: List[CampaignSummary]

