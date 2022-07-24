"""Module for Ingestion Validation Checking."""
import logging
import os

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, _context):
    """Main lambda handler for creating tables."""
    LOGGER.info(event)
    
    return event