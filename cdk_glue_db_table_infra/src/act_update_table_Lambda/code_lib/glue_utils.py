"""Module for holding Glue related methods."""
from distutils.log import error
import logging
import os
from urllib import response
import boto3
from botocore.exceptions import ClientError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def database_exists(db_name: str, region_name: str) -> bool:
    """Check if database exists in the given region.
    :param db_name: String -> of Database name in AWS Glue
    :param region_name: String -> of the region in the AWS Glue database
    :return: bool
    """
    
    try:
        client = boto3.client('glue', region_name=region_name)
        response = client.get_databases()
        database_list = response['DatabaseList']
        for database in database_list:
            if db_name == database['Name']:
                LOGGER.info("Database exists : %s", db_name)
                return True
        return False
    except ClientError as error:
        LOGGER.error("Error in getting Glue database: %s", error)
        raise error
    
    
def create_database(db_name: str, region_name: str) -> None:
    """Create database in the given region.
    :param db_name: String -> of Database name in AWS Glue
    :param region_name: String -> of the region in the AWS Glue database
    """
    
    try:
      client = boto3.client('glue', region_name=region_name)
      client.create_database(
          DatabaseInput={'Name': db_name})
      LOGGER.info("Database created: %s", db_name)
    except ClientError as error:
        LOGGER.error("Error in getting Glue database: %s", error)
        raise error
    
    
def create_table(db_name: str, table_name: dict, region_name: str) -> None:
    """Create table in the given database and region.
    :param db_name: String -> of Database name in AWS Glue
    :param table_name: dict -> of table in AWS Glue
    :param region_name: String -> of the region in the AWS Glue database
    """
    
    try:
        client = boto3.client('glue', region_name=region_name)
        client.create_table(
            DatabaseName=db_name,
            TableInput={
                'Name': table_name,
                'StorageDescriptor': {
                    'Columns': [
                        {'Name': 'asof_dt', 'Type': 'timestamp'},
                        {'Name': 'dataset_type', 'Type': 'string'},
                        {'Name': 'city', 'Type': 'string'},
                        {'Name': 'gl_code', 'Type': 'int'},
                    ],
                    'Location': f"s3://{os.environ['data_file_s3_location']}",
                    'InputFormat': (
                        'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputformat'    
                    ),
                    'OutputFormat': 
                        'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputformat',
                    'NumberOfBuckets': -1,
                    'SerdeInfo': {
                        'SerializationLibrary':
                            'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerde',
                        'Parameters': {
                            'serialization.format': '1'
                        }
                    }
                },
                'TableType': 'EXTERNAL_TABLE',
                'Parameters': {
                    'classification': 'parquet'
                }
            }
        )
        LOGGER.info("Table created: %s", table_name)
    except ClientError as error:
        LOGGER.error("Error in getting Glue database: %s", error)
        raise error  
    


