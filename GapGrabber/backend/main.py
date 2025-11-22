from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import slots, appointments, messages, campaigns, webhooks
from app.services.scheduler_service import start_scheduler, shutdown_scheduler
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="GapGrabber Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
@app.on_event("startup")
async def startup_event():
    init_db()
    start_scheduler()
    logger.info("Application started")


@app.on_event("shutdown")
async def shutdown_event():
    shutdown_scheduler()
    logger.info("Application shut down")


# Include routers
app.include_router(slots.router)
app.include_router(appointments.router)
app.include_router(messages.router)
app.include_router(campaigns.router)
app.include_router(webhooks.router)


@app.get("/")
async def root():
    return {"message": "GapGrabber Backend API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

