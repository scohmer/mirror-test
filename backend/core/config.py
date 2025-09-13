# Linux Mirror Testing Solution - Configuration

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Application settings
    app_name: str = "Linux Mirror Testing Solution"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    
    # CORS settings
    allowed_origins: List[str] = Field(default_factory=lambda: ["*"])
    
    # Database settings
    database_type: str = "sqlite"
    database_path: str = "./test_results.db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_username: str = "test_user"
    database_password: str = "test_password"
    
    # Test settings
    test_interval_minutes: int = 60
    test_timeout_seconds: int = 300
    max_concurrent_tests: int = 5
    
    # Container settings
    container_memory_mb: int = 1024
    container_cpu_cores: float = 1.0
    
    # Frontend settings
    frontend_refresh_interval_seconds: int = 5
    frontend_show_history: bool = True
    frontend_default_timeout: int = 300
    
    # Notification settings
    email_notifications_enabled: bool = False
    webhook_notifications_enabled: bool = False
    smtp_server: str = "smtp.example.com"
    smtp_port: int = 587
    email_recipients: List[str] = Field(default_factory=list)
    webhook_url: str = ""
    
    # Environment variable overrides
    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings
settings = Settings()
