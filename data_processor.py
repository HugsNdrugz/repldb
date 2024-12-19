# repldb/data_processor.py
import pandas as pd
import logging
from datetime import datetime
import pytz
from dateutil.parser import parse
from typing import Optional, Dict, Any
from pathlib import Path
from repldb.db_utils import create_connection, execute_query, close_connection, fetch_data
from repldb.data_loader import load_data_from_excel_text, convert_duration_to_seconds

DATABASE_FILE = "repldb.db"
BATCH_SIZE = 100

TABLE_SCHEMAS = {
    "contacts": {
        "columns": ["contact_id", "name", "phone_number", "email_id", "last_contacted", "last_contacted_dt"],
        "types": [int, str, str, str, str, datetime],
        "renames": {"email": "email_id", "last contacted": "last_contacted"}
    },
    "installedapps": {
        "columns": ["application_name", "package_name", "installed_date"],
        "types": [str, str, datetime],
        "renames": {}
    },
    "calls": {
        "columns": ["call_type", "time", "from_to", "duration", "location_id", "contact_id", "time_dt"],
        "types": [str, str, str, int, int, int, datetime],
        "renames": {"time": "time", "from/to": "from_to", "duration (sec)": "duration", "location": "location_text"}
    },
    "sms_messages": {
        "columns": ["sms_type", "time", "from_to", "text", "location_id", "contact_id", "time_dt"],
        "types": [str, str, str, str, int, int, datetime],
        "renames": {"location": "location_text"}
    },
    "chat_messages": {
        "columns": ["messenger", "time", "sender", "text", "contact_id", "time_dt"],
        "types": [str, str, str, str, int, datetime],
        "renames": {}
    },
    "keylogs": {
        "columns": ["application", "time", "text", "package_id", "time_dt"],
        "types": [str, str, str, str, datetime],
        "renames": {}
    },
     "locations": {
        "columns": ["location_id", "location_text"],
        "types": [int, str],
        "renames": {}
    }
}


def normalize_column_name(col: str) -> str:
    """Normalize column name for comparison"""
    return str(col).lower().strip().replace(' ', '_')

def identify_table(df: pd.DataFrame) -> Optional[str]:
    """Identifies the table based on the file's headers with flexible matching."""
    # Drop any unnamed columns first
    df = df.loc[:, ~df.columns.str.contains('^Unnamed:', na=False)]

    # Convert all headers to normalized form for comparison
    file_headers = {normalize_column_name(col) for col in df.columns if pd.notna(col)}
    logging.info(f"Found headers in file (after cleaning): {list(df.columns)}")
    logging.info(f"Normalized headers: {list(file_headers)}")

    # Early return if no valid headers
    if not file_headers:
        logging.error("No valid headers found in the file")
        return None

    for table, schema in TABLE_SCHEMAS.items():
        schema_headers = {normalize_column_name(col) for col in schema["columns"]}
        rename_headers = {normalize_column_name(col) for col in schema["renames"].keys()}

        logging.info(f"Checking table {table}")
        logging.info(f"Schema headers: {schema_headers}")
        logging.info(f"Rename headers: {rename_headers}")

        # Special handling for Keylog tables with more flexible matching
        if table in ['KeylogImport', 'Keylogs']:
            required_keylog_headers = {'application', 'time', 'text'}
            normalized_required = {normalize_column_name(h) for h in required_keylog_headers}

            # Check if required headers are present (allowing for partial matches)
            if any(any(req in header for header in file_headers) for req in normalized_required):
                logging.info(f"Matched {table} table based on required keylog headers")
                return table

        # For other tables, use a more lenient matching approach
        schema_match_ratio = len(schema_headers.intersection(file_headers)) / len(schema_headers)
        rename_match_ratio = len(rename_headers.intersection(file_headers)) / len(rename_headers)

        # Lower the threshold to 60% for more flexible matching
        if schema_match_ratio >= 0.6 or rename_match_ratio >= 0.6:
            logging.info(f"Matched {table} table with match ratio: {max(schema_match_ratio, rename_match_ratio):.2f}")
            return table

    logging.error("No matching table schema found")
    logging.error(f"Available headers: {list(df.columns)}")
    return None

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    schema = """
    CREATE TABLE IF NOT EXISTS Contacts (
        contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone_number TEXT,
        email_id TEXT,
        last_contacted TEXT,
        last_contacted_dt DATETIME,
        UNIQUE(name, phone_number, email_id)
    );

    CREATE TABLE IF NOT EXISTS InstalledApps (
        app_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_name TEXT NOT NULL,
        package_name TEXT UNIQUE NOT NULL,
        installed_date DATETIME
    );

    CREATE TABLE IF NOT EXISTS Calls (
        call_id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_type TEXT NOT NULL,
        time TEXT NOT NULL,
        time_dt DATETIME,
        from_to TEXT,
        duration INTEGER DEFAULT 0,
        location_id INTEGER,
        contact_id INTEGER,
         UNIQUE(call_type, time, from_to)
    );

    CREATE TABLE IF NOT EXISTS SMS_Messages (
        sms_id INTEGER PRIMARY KEY AUTOINCREMENT,
        sms_type TEXT NOT NULL,
        time TEXT NOT NULL,
        time_dt DATETIME,
        from_to TEXT,
        text TEXT,
        location_id INTEGER,
        contact_id INTEGER,
        UNIQUE(sms_type, time, from_to, text)
    );

    CREATE TABLE IF NOT EXISTS Chat_Messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        messenger TEXT NOT NULL,
        time TEXT NOT NULL,
        time_dt DATETIME,
        sender TEXT,
        text TEXT,
        contact_id INTEGER,
        UNIQUE(messenger, time, sender, text)
    );

    CREATE TABLE IF NOT EXISTS Keylogs (
        keylog_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application TEXT NOT NULL,
        time TEXT NOT NULL,
        time_dt DATETIME,
        text TEXT,
        package_id TEXT,
        UNIQUE(application, time, text)
    );

    CREATE TABLE IF NOT EXISTS Locations (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_text TEXT UNIQUE
    );
    """
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.executescript(schema)
        logging.info("Database initialized successfully")

def parse_timestamp_flexible(date_str: str, timezone: str = "UTC") -> Optional[datetime]:
    """Parse timestamp with flexible format handling"""
    if pd.isna(date_str) or not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    try:
        if isinstance(date_str, str):
            # Remove any extra whitespace
            date_str = date_str.strip()

            # Try parsing with dateutil parser
            try:
                dt = parse(date_str)
            except ValueError:
                # Try common formats if dateutil parser fails
                common_formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d %H:%M',
                    '%Y-%m-%d',
                    '%b %d, %I:%M %p',
                    '%b %d, %I:%M %p',
                    '%b %d, %I:%M %p',
                    '%b %d, %H:%M %p',
                    '%b %d, %H:%M',
                    '%b %d, %Y',
                    '%b %d, %Y %I:%M %p',
                    '%b %d, %Y %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S',
                    '%d/%m/%Y %H:%M',
                    '%d/%m/%Y',
                ]

                for fmt in common_formats:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Could not parse date string: {date_str}")

            # Set timezone if not present
            if dt.tzinfo is None:
                dt = pytz.timezone(timezone).localize(dt)
            return dt

        return None
    except Exception as e:
        logging.error(f"Failed to parse timestamp '{date_str}': {e}")
        return None

def validate_data(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    """Validates and cleans data according to schema"""
    schema = TABLE_SCHEMAS.get(table_name)
    if not schema:
        raise ValueError(f"Schema not found for table: {table_name}")

    # Store original column names for reference
    original_columns = df.columns
    logging.info(f"Original columns: {list(original_columns)}")

    # Create a mapping of normalized names to original names
    norm_to_orig = {normalize_column_name(col): col for col in original_columns}

    # Map schema columns to actual columns
    column_mapping = {}
    for expected_col in schema["columns"]:
        norm_expected = normalize_column_name(expected_col)
        if norm_expected in norm_to_orig:
            column_mapping[norm_to_orig[norm_expected]] = expected_col

    if not column_mapping:
        raise ValueError(f"No matching columns found in the data. Expected columns: {schema['columns']}")

    # Select and rename columns
    df = df[list(column_mapping.keys())].rename(columns=column_mapping)

    # Apply data type conversions and handle NULL constraints
    for col, dtype in zip(schema["columns"], schema["types"]):
        if col in df.columns:
            try:
                if dtype == datetime:
                    # Convert to datetime and handle invalid values
                    df[col] = df[col].apply(parse_timestamp_flexible)
                    # Drop rows where required datetime fields are null
                    if col in ['time', 'last_contacted', 'install_date']:
                        df = df.dropna(subset=[col])
                        logging.info(f"Dropped {len(df)} rows with null {col}")
                elif dtype == int:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                else:
                    # Handle text fields, replace NaN with empty string for optional text fields
                    if col not in ['name', 'application', 'text']:  # Required text fields
                        df[col] = df[col].fillna('').astype(str)
                    else:
                        # Drop rows where required text fields are null
                        df = df.dropna(subset=[col])
                        logging.info(f"Dropped {len(df)} rows with null {col}")
            except Exception as e:
                logging.error(f"Error converting column {col}: {e}")
                raise ValueError(f"Failed to process column {col}: {e}")

    return df

def process_and_insert_data(file_path: Path) -> Dict[str, Any]:
    """Process and import data with statistics tracking"""
    stats = {
        "total_rows": 0,
        "processed_rows": 0,
        "failed_rows": 0,
        "table_name": None
    }

    try:
        logging.info(f"Processing file: {file_path}")

        # Read the file
        if file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
            logging.info("Successfully read CSV file")
        else:
            # First attempt to read without skipping rows
            try:
                df = pd.read_excel(file_path, engine='openpyxl')
                # Check if first row contains metadata about tracking
                if any(col.lower().startswith('tracking smartphone') for col in df.columns.astype(str)):
                    logging.info("Detected metadata row, reading file again with header row 1")
                    df = pd.read_excel(file_path, engine='openpyxl', header=1)
                logging.info(f"Successfully read Excel file with headers: {list(df.columns)}")
            except Exception as e:
                logging.warning(f"Failed to read with openpyxl: {e}")
                try:
                    df = pd.read_excel(file_path, engine='xlrd')
                    if any(col.lower().startswith('tracking smartphone') for col in df.columns.astype(str)):
                        df = pd.read_excel(file_path, engine='xlrd', header=1)
                    logging.info(f"Successfully read Excel file with xlrd engine")
                except Exception as e:
                    logging.error(f"Failed to read Excel file with both engines: {e}")
                    raise

        stats["total_rows"] = len(df)

        # Identify table
        table_name = identify_table(df)
        if not table_name:
            raise ValueError("Could not identify table schema. Please check the file headers.")

        stats["table_name"] = table_name

        # Process data
        df = validate_data(df, table_name)

        # Insert data
        with create_connection(DATABASE_FILE) as conn:
            for i in range(0, len(df), BATCH_SIZE):
                batch = df.iloc[i:i + BATCH_SIZE]
                # Convert pandas DataFrame to list of dictionaries
                records = batch.to_dict(orient='records')
                for record in records:
                    if table_name == "calls":
                        location_text = record.pop("location_text", None)
                        contact_name = record.pop("from_to", None)
                        
                        location_id = None
                        if location_text:
                            location_id = fetch_or_create_location(conn, location_text)
                        record["location_id"] = location_id

                        contact_id = None
                        if contact_name:
                            contact_id = fetch_or_create_contact(conn, contact_name)
                        record["contact_id"] = contact_id
                    elif table_name == "sms_messages":
                        location_text = record.pop("location_text", None)
                        contact_name = record.pop("from_to", None)

                        location_id = None
                        if location_text:
                            location_id = fetch_or_create_location(conn, location_text)
                        record["location_id"] = location_id

                        contact_id = None
                        if contact_name:
                            contact_id = fetch_or_create_contact(conn, contact_name)
                        record["contact_id"] = contact_id
                    elif table_name == "chat_messages":
                        contact_name = record.pop("sender", None)
                        contact_id = None
                        if contact_name:
                            contact_id = fetch_or_create_contact(conn, contact_name)
                        record["contact_id"] = contact_id
                    
                    record["time_dt"] = record.pop("time", None)
                    
                    # Insert the record
                    placeholders = ', '.join('?' for _ in record.values())
                    columns = ', '.join(record.keys())
                    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    cursor = execute_query(conn, query, list(record.values()))
                    if not cursor:
                        stats["failed_rows"] += 1
                    else:
                        stats["processed_rows"] += 1
            
        return stats

    except Exception as e:
        stats["failed_rows"] = stats["total_rows"] - stats["processed_rows"]
        logging.error(f"Error processing file: {e}")
        raise

def fetch_or_create_location(conn: sqlite3.Connection, location_text: str) -> int:
    """Fetches the location ID or creates a new location if it doesn't exist."""
    query = "SELECT location_id FROM Locations WHERE location_text = ?"
    result = fetch_data(conn, query, (location_text,))
    if result:
        return result[0]['location_id']
    else:
        cursor = execute_query(conn, "INSERT INTO Locations (location_text) VALUES (?)", (location_text,))
        if cursor:
             return cursor.lastrowid
        else:
            return None

def fetch_or_create_contact(conn: sqlite3.Connection, contact_name: str) -> int:
    """Fetches the contact ID or creates a new contact if it doesn't exist."""
    query = "SELECT contact_id FROM Contacts WHERE name = ?"
    result = fetch_data(conn, query, (contact_name,))
    if result:
        return result[0]['contact_id']
    else:
        cursor = execute_query(conn, "INSERT INTO Contacts (name) VALUES (?)", (contact_name,))
        if cursor:
            return cursor.lastrowid
        else:
            return None

def main():
    init_db()