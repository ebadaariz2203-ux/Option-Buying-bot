from loguru import logger
import os

# Create logs folder if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logger
logger.add(
    "logs/trading_bot.log",
    rotation="10 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)