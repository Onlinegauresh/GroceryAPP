"""Application logger setup"""
import logging
import sys
from pythonjsonlogger import jsonlogger

# Create logger
logger = logging.getLogger("smartkirana")
logger.setLevel(logging.DEBUG)

# JSON format handler (for production)
json_handler = logging.StreamHandler(sys.stdout)
json_formatter = jsonlogger.JsonFormatter()
json_handler.setFormatter(json_formatter)

# Plain text handler (for development)
text_handler = logging.StreamHandler(sys.stdout)
text_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
text_handler.setFormatter(text_formatter)

# Add handlers
logger.addHandler(text_handler)
