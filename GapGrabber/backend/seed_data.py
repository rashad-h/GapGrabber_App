"""
Seed script to populate database with sample data for demo
"""
from app.database import SessionLocal, Customer, Appointment, Message
from datetime import datetime, timedelta
import random

# Sample data
customers_data = [
    {"name": "Sarah Johnson", "phone": "+1234567890"},
    {"name": "Mike Chen", "phone": "+1234567891"},
    {"name": "Lisa Park", "phone": "+1234567892"},
    {"name": "David Rodriguez", "phone": "+1234567893"},
    {"name": "Emma Wilson", "phone": "+1234567894"},
    {"name": "James Brown", "phone": "+1234567895"},
    {"name": "Olivia Martinez", "phone": "+1234567896"},
    {"name": "Noah Taylor", "phone": "+1234567897"},
    {"name": "Sophia Anderson", "phone": "+1234567898"},
    {"name": "Liam Thomas", "phone": "+1234567899"},
]

service_types = ["pipe repair", "boiler service", "drain unblocking", "leak fix", "installation", "emergency callout", "boiler service", "pipe repair", "drain unblocking", "installation"]

sample_messages = [
    "Thanks for fixing the leak so quickly!",
    "Looking forward to the boiler service!",
    "Can I reschedule?",
    "Perfect, see you then!",
    "Thanks so much for the emergency callout!",
    "Great service as always!",
    "I'll be there!",
    "Sounds good!",
]


def seed_database():
    db = SessionLocal()
    
    try:
        # Clear existing data (optional - comment out if you want to keep data)
        db.query(Message).delete()
        db.query(Appointment).delete()
        db.query(Customer).delete()
        db.commit()
        
        # Create customers
        customers = []
        for i, data in enumerate(customers_data):
            customer = Customer(
                name=data["name"],
                phone_number=data["phone"],
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 180))
            )
            db.add(customer)
            customers.append(customer)
        
        db.commit()
        
        # Create appointments (7-14 days in future) - ALL scheduled (cancellable)
        now = datetime.utcnow()
        for i, customer in enumerate(customers):
            # Future appointment
            future_date = now + timedelta(days=random.randint(7, 14))
            appointment = Appointment(
                customer_id=customer.id,
                scheduled_time=future_date,
                service_type=service_types[i],
                status="scheduled",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
            )
            db.add(appointment)
            
            # Additional future appointments (all scheduled, all cancellable)
            for j in range(random.randint(1, 2)):
                future_date2 = now + timedelta(days=random.randint(10, 21))
                appointment2 = Appointment(
                    customer_id=customer.id,
                    scheduled_time=future_date2,
                    service_type=service_types[(i + j) % len(service_types)],
                    status="scheduled",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 20))
                )
                db.add(appointment2)
        
        db.commit()
        
        # Create some message history
        for customer in customers[:7]:  # Messages for first 7 customers
            # 1-3 past messages
            for j in range(random.randint(1, 3)):
                message_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                message = Message(
                    customer_id=customer.id,
                    direction=random.choice(["inbound", "outbound"]),
                    content=random.choice(sample_messages),
                    timestamp=message_date
                )
                db.add(message)
        
        db.commit()
        
        print(f"✅ Seeded database with:")
        print(f"   - {len(customers)} customers")
        print(f"   - Multiple appointments per customer")
        print(f"   - Message history for some customers")
        
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

