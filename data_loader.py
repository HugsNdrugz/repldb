import os
import pandas as pd
from datetime import datetime
from database_utils import create_database_engine, get_or_create_record
from transforms import KeylogTransform, SmsMessageTransform, ChatMessageTransform, ContactTransform, CallTransform, InstalledAppTransform, LocationTransform
import logging
from sqlalchemy.exc import IntegrityError

table_mapping = {
    "keylogs": ["application", "time", "text"],
    "sms_messages": ["sms_type", "time", "from_to", "text", "location"],
    "chat_messages": ["messenger", "time", "sender", "text"],
    "contacts": ["name", "phone_number", "email_id", "last_contacted"],
    "calls": ["call_type", "time", "from_to", "duration_(sec)", "location"],
    "installedapps": ["application_name", "package_name", "installed_date"],
    "locations": ["location_text"]
}

transform_mapping = {
    "keylogs": KeylogTransform,
    "sms_messages": SmsMessageTransform,
    "chat_messages": ChatMessageTransform,
    "contacts": ContactTransform,
    "calls": CallTransform,
    "installedapps": InstalledAppTransform,
    "locations": LocationTransform
}
def _read_file(file_path):
    """Reads the data from the file, handling both excel and csv files"""
    df = None
    if file_path.lower().endswith(('.xls', '.xlsx')):
      print(f"Loading data as excel: {file_path}")
      try:
          df = pd.read_excel(file_path)
          # Remove the first row if it has only one column
          if df.shape[1] == 1:
              df = df.iloc[1:]
          # Reset the column headers after removing the meta row
          if not df.empty:
              df.columns = df.iloc[0]
              df = df[1:]
      except Exception as e:
          print(f"Error loading as excel: {e}")
          raise
    else:
      try:
        df = pd.read_csv(file_path)
      except Exception as e:
          print(f"Error loading csv: {e}")
          raise
    return df

def _identify_table(df, table_mapping):
    """Identifies which table the dataframe should be loaded into"""
    for table_name, expected_columns in table_mapping.items():
        if df is not None and all(col.lower().replace(' ', '_') in [expected_col.lower().replace(' ', '_') for expected_col in expected_columns] for col in df.columns):

            # Check if all expected columns are present after normalization
            normalized_expected_columns = [col.lower().replace(' ', '_') for col in expected_columns]
            normalized_df_columns = [col.lower().replace(' ', '_') for col in df.columns]
            if all(col in normalized_df_columns for col in normalized_expected_columns):
                return table_name
            else:
               missing_cols = [col for col in normalized_expected_columns if col not in normalized_df_columns]
               print(f"Error: Not all expected columns present in {table_name}. Missing columns: {missing_cols} for columns: {list(df.columns)}")
    return None
def load_and_clean_data(file_path, db_engine, table_mapping, transform_mapping):
    """Loads data from a CSV-like file, performs basic cleaning, and inserts into the appropriate table based on column names
    Args:
        file_path (str): The path to the CSV file.
        db_engine (sqlalchemy.engine.Engine): The SQLAlchemy database engine.
    Returns:
    None: The function insert data into the database.
    """
    try:
        df = _read_file(file_path)
    except Exception as e:
        print(f"Error reading file: {file_path}, {e}")
        return

    table_name = _identify_table(df, table_mapping)
    if not table_name:
         print(f"Error: Could not identify target table for columns: {list(df.columns)}")
         return

    transform_class = transform_mapping.get(table_name)
    if not transform_class:
        print(f"Error: No transform defined for table: {table_name}")
        return

    transform_instance = transform_class(db_engine)
    df = transform_instance.clean_columns(df)
    print(f"Loading data into table: {table_name}")
    df = transform_instance.transform(df)


    # Detect and Remove Duplicates
    original_length = len(df)
    df = df.drop_duplicates()
    duplicates_removed = original_length - len(df)
    if duplicates_removed > 0:
         print(f"Removed {duplicates_removed} duplicate rows from {table_name}")

    # Insert data into the database
    try:
        df.to_sql(table_name, db_engine, if_exists='append', index=False)
        print(f"Successfully loaded data into {table_name}")
    except IntegrityError as e:
         print(f"Integrity error when loading data into {table_name}: {e}")
         print(f"Continuing to load other files")
    except Exception as e:
          print(f"Error when loading data into table: {table_name}: {e}")

    #Save the file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(file_path), "cleaned_output")
    if not os.path.exists(output_dir):
       os.makedirs(output_dir)
    filename = os.path.basename(file_path)
    base_name, _ = os.path.splitext(filename)
    output_file = os.path.join(output_dir, f"{base_name}_cleaned_{timestamp}.csv")
    df.to_csv(output_file, index=False)