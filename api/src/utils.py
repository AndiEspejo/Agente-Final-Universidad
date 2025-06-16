"""
Utility functions for the sales/inventory system.

This module provides helper functions for:
- Loading environment variables
- Initializing the Gemini API
- Setting up logging
- Common configuration tasks
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import google.generativeai as genai
import structlog
from dotenv import load_dotenv


def load_environment() -> None:
    """
    Load environment variables from .env file.

    Searches for .env file in current directory and parent directories.
    """
    # Look for .env file starting from current directory
    current_dir = Path.cwd()
    env_file = None

    # Search up the directory tree for .env file
    for parent in [current_dir] + list(current_dir.parents):
        potential_env = parent / ".env"
        if potential_env.exists():
            env_file = potential_env
            break

    if env_file:
        load_dotenv(env_file)
        print(f"Loaded environment from: {env_file}")
    else:
        print("No .env file found, using system environment variables")


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get environment variable with optional default and required validation.

    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required

    Returns:
        Environment variable value

    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)

    if required and not value:
        raise ValueError(f"Required environment variable '{key}' not found")

    return value


def initialize_gemini_api() -> genai.GenerativeModel:
    """
    Initialize and configure the Google Gemini API.

    Returns:
        Configured Gemini GenerativeModel instance

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    api_key = get_env_var("GEMINI_API_KEY", required=True)

    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Initialize the model with current stable model name
    model = genai.GenerativeModel("gemini-1.5-flash")

    logging.info("Gemini API initialized successfully")
    return model


def setup_logging(
    name: str = "app", log_level: str = None, log_format: str = "json"
) -> structlog.stdlib.BoundLogger:
    """
    Set up structured logging for the application.

    Args:
        name: Logger name (usually module name)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Log format ('json' or 'console')

    Returns:
        Configured logger instance
    """
    if log_level is None:
        log_level = get_env_var("LOG_LEVEL", "INFO")

    # Configure structlog
    if log_format == "json":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set the logging level
    logging.basicConfig(format="%(message)s", level=getattr(logging, log_level.upper()))

    logger = structlog.get_logger(name)
    logger.info("Logging initialized", level=log_level, format=log_format)

    return logger


def get_database_url() -> str:
    """
    Get database URL from environment with fallback to SQLite.

    Returns:
        Database connection URL
    """
    return get_env_var("DATABASE_URL", "sqlite:///./sales_inventory.db")


def get_jwt_config() -> Dict[str, Any]:
    """
    Get JWT configuration from environment variables.

    Returns:
        Dictionary with JWT configuration
    """
    return {
        "secret_key": get_env_var("JWT_SECRET_KEY", required=True),
        "algorithm": get_env_var("JWT_ALGORITHM", "HS256"),
        "access_token_expire_minutes": int(
            get_env_var("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        ),
    }


def get_ffmpeg_path() -> str:
    """
    Get FFmpeg executable path.

    Returns:
        Path to FFmpeg executable

    Raises:
        RuntimeError: If FFmpeg is not found
    """
    # Check environment variable first
    ffmpeg_path = get_env_var("FFMPEG_PATH")

    if ffmpeg_path and Path(ffmpeg_path).exists():
        return ffmpeg_path

    # Try to find FFmpeg in PATH
    import shutil

    ffmpeg_path = shutil.which("ffmpeg")

    if not ffmpeg_path:
        raise RuntimeError(
            "FFmpeg not found. Please install FFmpeg or set FFMPEG_PATH environment variable"
        )

    return ffmpeg_path


def get_gemini_model() -> genai.GenerativeModel:
    """
    Get a configured Gemini model instance.

    Returns:
        Configured Gemini GenerativeModel instance
    """
    return initialize_gemini_api()


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        True if all required variables are present

    Raises:
        ValueError: If any required variable is missing
    """
    required_vars = ["GEMINI_API_KEY", "JWT_SECRET_KEY"]

    missing_vars = []
    for var in required_vars:
        if not get_env_var(var):
            missing_vars.append(var)

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    return True


# Initialize environment and logging when module is imported
load_environment()
logger = setup_logging("utils")
