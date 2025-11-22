# 🧰 GapGrabber - Smart Cancellation Manager

AI-powered slot-filling system for small businesses. Automatically fills empty appointment slots by intelligently reaching out to existing customers via WhatsApp.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Twilio account (for WhatsApp)
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the `backend` directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
   TEST_WHATSAPP_NUMBER=+1234567890
   DATABASE_URL=sqlite:///./database.db
   LOG_LEVEL=INFO
   ```

5. **Initialize database:**
   ```bash
   python seed_data.py
   ```

6. **Start the backend server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The backend will be available at: http://localhost:8000
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend/plumber-pro-main
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at: http://localhost:8080

## 📋 How to Use

### 1. View Schedule
- Open http://localhost:8080
- Click on the "Schedule" tab (📅 icon)
- See all scheduled appointments

### 2. Cancel & Fill a Slot
- Click "Cancel Slot" on any scheduled appointment
- Enter:
  - **Reason**: Why the slot opened (e.g., "Customer cancelled last minute")
  - **Discount %**: Optional discount to offer (e.g., 10%)
  - **Wait Time**: Minutes to wait before contacting next batch (e.g., 30)
- Click "Start Contacting"
- The system will:
  - Cancel the appointment
  - Find customers with future appointments
  - Evaluate them using AI
  - Send personalized WhatsApp messages to top 3 candidates
  - Create a campaign to track progress

### 3. View Campaigns (Gaps)
- Click on the "Gaps" tab (🔄 icon)
- See all active campaigns
- Click on a campaign to see:
  - Customers contacted
  - Their response status
  - Messages sent

### 4. View Customer Messages
- From a campaign detail page, click on any customer
- See the full conversation history
- Messages are organized chronologically

### 5. Test Webhook (Simulate Customer Response)
- Use Postman or curl to send a webhook:
  ```bash
  curl -X POST http://localhost:8000/webhooks/twilio \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "From=whatsapp:+1234567890" \
    -d "Body=Yes, I can do tomorrow at 2pm!" \
    -d "MessageSid=SMtest123"
  ```
- The system will:
  - Analyze the response with AI
  - Send a personalized confirmation
  - Update campaign status
  - Notify other customers (saved to DB, not sent via WhatsApp)

## 🏗 Architecture

### Backend (FastAPI + Python)
- **Database**: SQLite (local file-based)
- **AI**: OpenAI GPT-4o-mini for customer evaluation and message generation
- **Messaging**: Twilio WhatsApp API
- **Scheduling**: APScheduler for batch timing
- **API**: RESTful endpoints for frontend integration

### Frontend (React + TypeScript + Vite)
- **Framework**: React with TypeScript
- **UI**: Tailwind CSS + shadcn/ui components
- **Routing**: React Router
- **State**: React Query for API state management

## 📡 API Endpoints

### Appointments
- `GET /api/appointments` - List all appointments
- `POST /api/appointments/{id}/cancel-and-fill` - Cancel appointment and trigger campaign

### Campaigns
- `GET /api/campaigns` - List all campaigns
- `GET /api/campaigns/{id}` - Get campaign details

### Messages
- `GET /api/messages` - Get messages (organized by customer)
- `GET /api/messages?campaign_id={id}` - Get messages for a campaign
- `GET /api/messages?customer_id={id}` - Get messages for a customer

### Webhooks
- `POST /webhooks/twilio` - Receive WhatsApp messages from Twilio

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `TWILIO_ACCOUNT_SID` - Twilio Account SID (required)
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token (required)
- `TWILIO_WHATSAPP_NUMBER` - Your Twilio WhatsApp number (required)
- `TEST_WHATSAPP_NUMBER` - Test number for demo (required)
- `DATABASE_URL` - Database connection string (default: sqlite:///./database.db)
- `LOG_LEVEL` - Logging level (default: INFO)

**Frontend:**
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## 🧪 Testing

### Reset Database
```bash
cd backend
source venv/bin/activate
python -c "
from app.database import Base, engine
from seed_data import seed_database
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
seed_database()
print('✅ Database reset!')
"
```

### Test API Endpoints
- Use Postman collection: `backend/postman_collection.json`
- Or use curl commands (see `backend/DASHBOARD_FLOW.md`)

## 📁 Project Structure

```
GapGrabber/
├── backend/
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── database.py      # Database models
│   │   └── config.py        # Configuration
│   ├── main.py              # FastAPI app entry point
│   ├── seed_data.py         # Database seeding
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── plumber-pro-main/
│       ├── src/
│       │   ├── pages/       # React pages
│       │   ├── components/  # UI components
│       │   └── lib/         # API client
│       └── package.json     # Node dependencies
└── README.md
```

## 🎯 Features

- ✅ **Autonomous Campaign Management** - Automatically contacts customers when slots open
- ✅ **AI-Powered Evaluation** - Uses OpenAI to evaluate customer fit
- ✅ **Personalized Messages** - Generates unique messages for each customer
- ✅ **Batch Processing** - Contacts customers in batches with configurable wait times
- ✅ **Real-time Updates** - Webhook-based immediate response handling
- ✅ **Beautiful Dashboard** - Modern React UI for monitoring campaigns
- ✅ **Message History** - Full conversation history organized by customer

## 🐛 Troubleshooting

### Backend won't start
- Check that virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check `.env` file exists and has all required variables

### Frontend won't start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check that backend is running on port 8000

### No campaigns showing
- Check browser console (F12) for errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS configuration in `backend/main.py`

### WhatsApp messages not sending
- Verify Twilio credentials in `.env`
- Check Twilio WhatsApp number format: `whatsapp:+1234567890`
- Verify test number is correct: `TEST_WHATSAPP_NUMBER`

## 📝 License

MIT License - feel free to use and modify for your own projects!

## 🙏 Acknowledgments

- **OpenAI** - For powerful language models
- **Twilio** - For WhatsApp messaging infrastructure
- **FastAPI** - For the excellent Python web framework
- **React** - For the frontend framework
