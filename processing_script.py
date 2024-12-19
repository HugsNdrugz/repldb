 import os
 import pandas as pd
 import re
 from datetime import datetime
 from sqlalchemy import create_engine, text
 from upload_script import UPLOAD_FOLDER

 db_path = "my_database.db"
 db_engine = create_engine(f"sqlite:///{db_path}")

 table_mapping = {
     "keylogs": ["application", "time", "text"],
     "sms_messages": ["sms_type", "time", "from_to", "text", "location"],
     "chat_messages": ["messenger", "time", "sender", "text"],
     "contacts": ["name", "phone_number", "email_id", "last_contacted"],
     "calls": ["call_type", "time", "from_to", "duration_(sec)", "location"],
     "installedapps": ["application_name", "package_name", "installed_date"],
     "locations": ["location_text"]
 }

 def main():
     """Main function that loops through uploaded files and runs data processing."""
     #Create engine
     db_path = "my_database.db"
     db_engine = create_engine(f"sqlite:///{db_path}")

     # Get a list of all files in the uploads folder
     if os.path.exists(UPLOAD_FOLDER):
        for filename in os.listdir(UPLOAD_FOLDER):
            if not filename.startswith("cleaned") and not filename.endswith(".py"):
              file_path = os.path.join(UPLOAD_FOLDER, filename)
              load_and_clean_data(file_path, db_engine, table_mapping)
     else:
         print(f"Error: Directory not found: {UPLOAD_FOLDER}")
 ```
*   `data_loader.py`
*   Update the file to not include any transforms or database calls

  ```python
 import os
 import pandas as pd
 from datetime import datetime
 from database_utils import create_database_engine, get_or_create_record
 from transforms import KeylogTransform, SmsMessageTransform, ChatMessageTransform, ContactTransform, CallTransform, InstalledAppTransform, LocationTransform
 import logging

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

 def load_and_clean_data(file_path, db_engine, table_mapping, transform_mapping):
     """Loads data from a CSV-like file, performs basic cleaning, and inserts into the appropriate table based on column names
     Args:
         file_path (str): The path to the CSV file.
         db_engine (sqlalchemy.engine.Engine): The SQLAlchemy database engine.
     Returns:
     None: The function insert data into the database.
     """
     try:
         df = None
         # Check if the file is an excel file
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
                 print(f"Error loading data from {file_path}: {e}")
                 return
         else:
            try:
                 df = pd.read_csv(file_path)
            except Exception as e:
                 print(f"Error loading data from {file_path}: {e}")
                 return
         
         transform_instance = None
         # Convert all column names to lowercase and replace spaces with underscores
         for table_name, expected_columns in table_mapping.items():
             if df is not None and all(col.lower().replace(' ', '_') in [expected_col.lower().replace(' ', '_') for expected_col in expected_columns] for col in df.columns):
                 
                 # Check if all expected columns are present after normalization
                 normalized_expected_columns = [col.lower().replace(' ', '_') for col in expected_columns]
                 normalized_df_columns = [col.lower().replace(' ', '_') for col in df.columns]
                 if all(col in normalized_df_columns for col in normalized_expected_columns):
                   transform_class = transform_mapping.get(table_name)
                   if transform_class:
                       transform_instance = transform_class(db_engine)
                       df = transform_instance.clean_columns(df)
                       print(f"Loading data into table: {table_name}")
                       df = transform_instance.transform(df)
                       break
                 else:
                   missing_cols = [col for col in normalized_expected_columns if col not in normalized_df_columns]
                   print(f"Error: Not all expected columns present in {table_name}. Missing columns: {missing_cols} for columns: {list(df.columns)}")
         if transform_instance is None:
               print(f"Error: Could not identify target table for columns: {list(df.columns)}")
               return

         # Detect and Remove Duplicates
         original_length = len(df)
         df = df.drop_duplicates()
         duplicates_removed = original_length - len(df)
         if duplicates_removed > 0:
              print(f"Removed {duplicates_removed} duplicate rows from {table_name}")

         # Insert data into the database
         df.to_sql(table_name, db_engine, if_exists='append', index=False)
         print(f"Successfully loaded data into {table_name}")

         #Save the file name
         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
         output_dir = os.path.join(os.path.dirname(file_path), "cleaned_output")
         if not os.path.exists(output_dir):
            os.makedirs(output_dir)
         filename = os.path.basename(file_path)
         base_name, _ = os.path.splitext(filename)
         output_file = os.path.join(output_dir, f"{base_name}_cleaned_{timestamp}.csv")
         df.to_csv(output_file, index=False)
     except Exception as e:
          print(f"Error loading data from {file_path}: {e}")
 ```