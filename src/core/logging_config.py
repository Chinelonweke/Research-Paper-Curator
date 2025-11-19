"""
Logging configuration using loguru
"""
import sys
from loguru import logger
from src.core.config import settings

# Remove default logger
logger.remove()

# Add console logger with colors
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

# Add file logger
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
    level=settings.log_level,
    rotation="100 MB",
    retention="30 days",
    compression="zip"
)

# Export as app_logger for compatibility
app_logger = logger

# Log startup
app_logger.info("✓ Logging system initialized")
