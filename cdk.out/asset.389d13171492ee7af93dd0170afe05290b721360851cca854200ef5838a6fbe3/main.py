"""Module for Ingestion Validation Checking."""
import logging
import os
from code_lib.glue_utils import database_exists, create_database, create_table

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def lambda_handler(event, _context):
    """Main lambda handler for creating tables."""
    LOGGER.info(event)
    incoming_asof_date = event['asof_date']
    logging.info(incoming_asof_date)
    year, month, day = incoming_asof_date.split('-')[-3:]
    region = os.environ['region']
    database_name = os.environ['database_name']
    table_name = os.environ['table_name']
    
    if not database_exists(database_name, region):
        create_database(database_name, region)
        create_table(database_name, table_name, region)
    
    return event