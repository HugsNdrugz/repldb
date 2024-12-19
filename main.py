import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from data_loader import load_and_clean_data, table_mapping, transform_mapping
from database_utils import create_database_engine, create_table, table_exists, create_indexes
from upload_script import UPLOAD_FOLDER
import logging

db_path = "my_database.db"

# Table creation SQL statements
create_keylogs_sql = """
    CREATE TABLE IF NOT EXISTS keylogs (
        application TEXT,
        time TEXT,
        time_dt DATETIME,
        text TEXT,
        package_id TEXT,
        UNIQUE(application, time, text)
    );
"""

create_sms_messages_sql = """
    CREATE TABLE IF NOT EXISTS sms_messages (
        sms_type TEXT,
        time TEXT,
        time_dt DATETIME,
        from_to TEXT,
        text TEXT,
        location_id INTEGER,
        contact_id INTEGER,
        UNIQUE(sms_type, time, from_to, text),
        FOREIGN KEY (location_id) REFERENCES locations(location_id),
        FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
    );
"""

create_chat_messages_sql = """
    CREATE TABLE IF NOT EXISTS chat_messages (
        messenger TEXT,
        time TEXT,
        time_dt DATETIME,
        sender TEXT,
        text TEXT,
        contact_id INTEGER,
        UNIQUE(messenger, time, sender, text)
    );
"""

create_contacts_sql = """
    CREATE TABLE IF NOT EXISTS contacts (
        contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone_number TEXT,
        email_id TEXT,
        last_contacted TEXT,
        last_contacted_dt DATETIME,
        UNIQUE(name, phone_number, email_id)
    );
"""

create_calls_sql = """
    CREATE TABLE IF NOT EXISTS calls (
        call_type TEXT,
        time TEXT,
        time_dt DATETIME,
        from_to TEXT,
        duration INTEGER,
        location_id INTEGER,
        contact_id INTEGER,
         UNIQUE(call_type, time, from_to),
        FOREIGN KEY (location_id) REFERENCES locations(location_id),
        FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
    );
"""

create_installedapps_sql = """
    CREATE TABLE IF NOT EXISTS installedapps (
        application_name TEXT,
        package_name TEXT,
        installed_date DATETIME,
        UNIQUE(application_name, package_name)
    );
"""

create_locations_sql = """
    CREATE TABLE IF NOT EXISTS locations (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_text TEXT UNIQUE
    );
"""

table_creation_mapping = {
  "keylogs": create_keylogs_sql,
  "sms_messages": create_sms_messages_sql,
  "chat_messages": create_chat_messages_sql,
  "contacts": create_contacts_sql,
  "calls": create_calls_sql,
  "installedapps": create_installedapps_sql,
  "locations": create_locations_sql
}

index_sql = [
    """CREATE INDEX IF NOT EXISTS idx_keylogs_by_time ON keylogs(time_dt);""",
    """CREATE INDEX IF NOT EXISTS idx_sms_messages_by_time ON sms_messages(time_dt);""",
    """CREATE INDEX IF NOT EXISTS idx_sms_messages_by_contact ON sms_messages(contact_id);""",
    """CREATE INDEX IF NOT EXISTS idx_chat_messages_by_time ON chat_messages(time_dt);""",
    """CREATE INDEX IF NOT EXISTS idx_chat_messages_by_contact ON chat_messages(contact_id);""",
    """CREATE INDEX IF NOT EXISTS idx_contacts_by_name ON contacts(name);""",
    """CREATE INDEX IF NOT EXISTS idx_calls_by_time ON calls(time_dt);""",
    """CREATE INDEX IF NOT EXISTS idx_calls_by_contact ON calls(contact_id);""",
    """CREATE INDEX IF NOT EXISTS idx_installedapps_by_application ON installedapps(application_name);""",
    """CREATE INDEX IF NOT EXISTS idx_locations_by_location_text ON locations(location_text);"""
]
def main():
    """Main function that initializes the database, creates tables and indexes if they don't exist,
        and processes the files in the uploads folder.
    """
    #Create engine
    logging.info("Starting main.py")
    db_engine = create_database_engine(db_path)
    logging.info("Database engine created.")

    # Create the other tables if they do not exist
    for table_name, create_sql in table_creation_mapping.items():
      if not table_exists(db_engine, table_name):
          try:
             create_table(db_engine, table_name, create_sql)
          except Exception as e:
            logging.error(f"The {table_name} could not be created: {e}. Exiting....")
            return
    # Create Indexes
    try:
        create_indexes(db_engine, index_sql)
    except Exception as e:
        logging.error(f"The indexes could not be created: {e}. Exiting...")
        return

    # Get a list of all files in the uploads folder
    if os.path.exists(UPLOAD_FOLDER):
       for filename in os.listdir(UPLOAD_FOLDER):
           if not filename.startswith("cleaned") and not filename.endswith(".py"):
             file_path = os.path.join(UPLOAD_FOLDER, filename)
             try:
                 load_and_clean_data(file_path, db_engine, table_mapping, transform_mapping)
             except Exception as e:
                logging.error(f"Error loading and cleaning file: {file_path}: {e}")
    else:
        logging.error(f"Error: Directory not found: {UPLOAD_FOLDER}")
    logging.info("Finished processing files.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()