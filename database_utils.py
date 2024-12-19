import os
from sqlalchemy import create_engine, text, exc, select, insert, column
import pandas as pd
import logging

def create_database_engine(db_path):
    """Creates a database engine from the given database path."""
    return create_engine(f"sqlite:///{db_path}")


def create_table(db_engine, table_name, create_sql):
    """Creates a table if it does not exist."""
    try:
        with db_engine.connect() as conn:
            conn.execute(text(create_sql))
        logging.info(f"Table '{table_name}' created successfully.")
        return True
    except exc.SQLAlchemyError as e:
        logging.error(f"Error creating table '{table_name}': {e}")
        raise


def table_exists(db_engine, table_name):
    """Checks if a table exists in the database."""
    try:
        with db_engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';
            """)).fetchone()
            return result is not None
    except exc.SQLAlchemyError as e:
         logging.error(f"Error checking if table '{table_name}' exists: {e}")
         raise

def get_or_create_record(db_engine, table_name, column_name, record_text, id_column_name):
    """Retrieves the id of a record or creates a new one if it does not exist."""
    if pd.isna(record_text):
        return None
    try:
        with db_engine.connect() as conn:
            query = select(column(id_column_name)).where(column(column_name) == record_text).select_from(table_name)
            result = conn.execute(query).fetchone()
            if result:
                return result[0]
            else:
                insert_query = insert(table(table_name)).values({column_name: record_text})
                result = conn.execute(insert_query)
                return result.lastrowid
    except exc.SQLAlchemyError as e:
         logging.error(f"Error getting or creating record in table {table_name} column {column_name}: {e}")
         raise


def create_indexes(db_engine, index_sql):
    """Creates indexes in the database."""
    try:
        with db_engine.connect() as conn:
            for sql in index_sql:
                conn.execute(text(sql))
        logging.info("Indexes created successfully.")
        return True
    except exc.SQLAlchemyError as e:
        logging.error(f"Error creating indexes: {e}")
        raise