"""
Configuration Utilities

Provides configuration loading and management for the Keap MCP server.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for Keap MCP Server"""
    
    # Default values
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 5000
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_FILE = "keap_mcp_server.log"
    
    def __init__(self, env_file: Optional[str] = None):
        """Initialize the config
        
        Args:
            env_file: Path to .env file (optional)
        """
        # Load environment variables
        load_dotenv(env_file)
        
        # Server settings
        self.host = os.getenv("KEAP_MCP_HOST", self.DEFAULT_HOST)
        self.port = int(os.getenv("KEAP_MCP_PORT", self.DEFAULT_PORT))
        
        # Logging settings
        self.log_level = os.getenv("KEAP_MCP_LOG_LEVEL", self.DEFAULT_LOG_LEVEL)
        self.log_file = os.getenv("KEAP_MCP_LOG_FILE", self.DEFAULT_LOG_FILE)
        
        # API settings
        self.api_key = os.getenv("KEAP_API_KEY")
        self.api_base_url = os.getenv("KEAP_API_BASE_URL", "https://api.infusionsoft.com/crm/rest/v1")
        
        # Cache settings
        self.cache_enabled = os.getenv("KEAP_MCP_CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("KEAP_MCP_CACHE_TTL", "3600"))
        
        # Validate required settings
        self._validate()
    
    def _validate(self):
        """Validate the configuration settings"""
        if not self.api_key:
            logger.warning("KEAP_API_KEY is not set. The server will attempt to load from config file.")
    
    def as_dict(self) -> Dict[str, Any]:
        """Get the configuration as a dictionary
        
        Returns:
            Dict with configuration settings
        """
        return {
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "api_base_url": self.api_base_url,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl
        }
    
    def get_log_level_int(self) -> int:
        """Get the log level as an integer
        
        Returns:
            Logging level integer
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        return level_map.get(self.log_level.upper(), logging.INFO)


# Create a default config instance
default_config = Config()
