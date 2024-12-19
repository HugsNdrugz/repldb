import os
from sqlalchemy import create_engine, text

db_path = "my_database.db"

# Table creation SQL statements
create_locations_sql = """
    CREATE TABLE IF NOT EXISTS locations (
        location_id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_text TEXT UNIQUE
    )
"""

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
        UNIQUE(sms_type, time, from_to, text)
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
         UNIQUE(call_type, time, from_to)
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

table_creation_mapping = {
  "locations": create_locations_sql,
  "keylogs": create_keylogs_sql,
  "sms_messages": create_sms_messages_sql,
  "chat_messages": create_chat_messages_sql,
  "contacts": create_contacts_sql,
  "calls": create_calls_sql,
  "installedapps": create_installedapps_sql
}


def create_database(db_path):
    """Creates the database and tables if they don't exist."""
    engine = create_engine(f"sqlite:///{db_path}")
    try:
        with engine.connect() as conn:
            for table_name, create_sql in table_creation_mapping.items():
                conn.execute(text(create_sql))
                print(f"Table '{table_name}' created successfully.")
        print("Database and tables created successfully.")
    except Exception as e:
        print(f"Error creating database or tables: {e}")


if __name__ == "__main__":
    create_database(db_path)