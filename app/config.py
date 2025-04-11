"""
Configuration management for the application
"""
import json
import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    """
    Application settings derived from config.json or environment variables
    
    Environment variables take precedence over config file values
    """
    origins: List[str] = ["http://localhost:8000", "http://127.0.0.1:8000"]
    tmp_path: str = "./dtmp/"
    upload_tmp_path: str = "./utmp/"
    share_path: str = "./share/"
    port: int = 8000
    log_level: str = "INFO"
    
    @validator("tmp_path", "upload_tmp_path", "share_path")
    def validate_paths(cls, v):
        """Ensure paths end with a trailing slash"""
        if not v.endswith("/"):
            v = v + "/"
        return v

@lru_cache()
def get_settings() -> Settings:
    """
    Load settings from config file and/or environment variables
    Using lru_cache to avoid reloading config on each call
    """
    config_path = os.environ.get("CONFIG_PATH", "./config/config.json")
    
    # Default settings
    settings_dict = {}
    
    # Try to load from config file
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config_data = json.load(f)
                settings_dict.update(config_data)
    except Exception as e:
        print(f"Error loading config file: {e}")
    
    # Create settings object (env vars will override config file)
    return Settings(**settings_dict)