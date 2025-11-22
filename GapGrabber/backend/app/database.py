from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import settings

Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="customer")
    messages = relationship("Message", back_populates="customer")
    campaign_outreach = relationship("CampaignOutreach", back_populates="customer")


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    service_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # 'scheduled', 'cancelled', 'completed'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="appointments")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    direction = Column(String, nullable=False)  # 'inbound', 'outbound'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    twilio_sid = Column(String, nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="messages")


class SlotFillCampaign(Base):
    __tablename__ = "slot_fill_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    cancelled_slot_time = Column(DateTime, nullable=False)
    service_type = Column(String, nullable=False)
    discount_percentage = Column(Integer, nullable=False)
    wait_time_minutes = Column(Integer, nullable=False)
    custom_context = Column(Text, nullable=True)
    status = Column(String, nullable=False)  # 'active', 'filled', 'expired'
    filled_by_customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    outreach_attempts = relationship("CampaignOutreach", back_populates="campaign")


class CampaignOutreach(Base):
    __tablename__ = "campaign_outreach"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("slot_fill_campaigns.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    batch_number = Column(Integer, nullable=False)
    message_sent = Column(Text, nullable=False)
    status = Column(String, nullable=False)  # 'sent', 'accepted', 'declined', 'notified_filled'
    sent_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    
    # Relationships
    campaign = relationship("SlotFillCampaign", back_populates="outreach_attempts")
    customer = relationship("Customer", back_populates="campaign_outreach")


# Database setup
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

