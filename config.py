"""
Configuration management for API Tester MCP Server
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Server settings
    SERVER_NAME: str = "api-tester"
    SERVER_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API Testing settings
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", 30))
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", 50))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", 5))
    
    # Request settings
    DEFAULT_HEADERS: Dict[str, str] = {
        "User-Agent": f"{SERVER_NAME}/{SERVER_VERSION}",
        "Accept": "application/json, text/plain, */*"
    }
    
    # Storage settings
    SAVE_REQUESTS_TO_FILE: bool = os.getenv("SAVE_REQUESTS_TO_FILE", "false").lower() == "true"
    REQUESTS_FILE_PATH: str = os.getenv("REQUESTS_FILE_PATH", "saved_requests.json")
    HISTORY_FILE_PATH: str = os.getenv("HISTORY_FILE_PATH", "request_history.json")
    
    # Security settings
    ALLOWED_DOMAINS: list = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else []
    BLOCKED_DOMAINS: list = os.getenv("BLOCKED_DOMAINS", "").split(",") if os.getenv("BLOCKED_DOMAINS") else []
    
    # Response limits
    MAX_RESPONSE_SIZE: int = int(os.getenv("MAX_RESPONSE_SIZE", 10 * 1024 * 1024))  # 10MB
    RESPONSE_PREVIEW_LENGTH: int = int(os.getenv("RESPONSE_PREVIEW_LENGTH", 1000))
    
    @classmethod
    def is_url_allowed(cls, url: str) -> bool:
        """Check if URL is allowed based on domain restrictions"""
        if not cls.ALLOWED_DOMAINS and not cls.BLOCKED_DOMAINS:
            return True
            
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        
        # Check blocked domains first
        if cls.BLOCKED_DOMAINS:
            for blocked in cls.BLOCKED_DOMAINS:
                if blocked.strip() and blocked.strip().lower() in domain:
                    return False
        
        # Check allowed domains
        if cls.ALLOWED_DOMAINS:
            for allowed in cls.ALLOWED_DOMAINS:
                if allowed.strip() and allowed.strip().lower() in domain:
                    return True
            return False  # If allowed domains specified, must match one
        
        return True
    
    @classmethod
    def get_default_headers(cls) -> Dict[str, str]:
        """Get default headers for requests"""
        return cls.DEFAULT_HEADERS.copy()
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        if cls.DEFAULT_TIMEOUT <= 0:
            print("Warning: DEFAULT_TIMEOUT must be positive")
            return False
            
        if cls.MAX_HISTORY <= 0:
            print("Warning: MAX_HISTORY must be positive")
            return False
            
        if cls.MAX_RESPONSE_SIZE <= 0:
            print("Warning: MAX_RESPONSE_SIZE must be positive")
            return False
            
        return True

config = Config()

# Environment-specific configurations
ENVIRONMENTS = {
    "local": {
        "name": "Local Development",
        "base_url": "http://localhost:3000",
        "timeout": 10
    },
    "dev": {
        "name": "Development",
        "base_url": "https://dev-api.example.com",
        "timeout": 15
    },
    "staging": {
        "name": "Staging",
        "base_url": "https://staging-api.example.com", 
        "timeout": 20
    },
    "prod": {
        "name": "Production",
        "base_url": "https://api.example.com",
        "timeout": 30
    }
}

def get_environment_config(env_name: str) -> Dict[str, Any]:
    """Get configuration for a specific environment"""
    return ENVIRONMENTS.get(env_name, {})

def list_environments() -> list:
    """List all available environments"""
    return list(ENVIRONMENTS.keys())

if not config.validate_config():
    print("Warning: Configuration validation failed!")