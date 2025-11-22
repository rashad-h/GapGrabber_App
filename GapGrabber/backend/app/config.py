from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_whatsapp_number: str
    database_url: str = "sqlite:///./database.db"
    log_level: str = "INFO"
    test_whatsapp_number: str  # Required from TEST_WHATSAPP_NUMBER in .env
    
    class Config:
        env_file = [".env", "../secrets.env"]  # Check both locations
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env


settings = Settings()

