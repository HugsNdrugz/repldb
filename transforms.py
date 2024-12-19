import pandas as pd
from datetime import datetime
from database_utils import get_or_create_record
import logging
from dateutil import parser

def parse_datetime(date_string, format_string = '%b %e, %I:%M %p'):
    """ Parses a date string into a datetime object, handling any errors that occur
    Args:
        date_string (str): The date string to parse.
        format_string (str): The format of the date

    Returns:
        datetime: The parsed date object.
        None: If date string is missing, or does not follow format
    """
    if pd.isna(date_string):
       return None
    try:
        # Attempt to parse with dateutil.parser which handles many formats
        return parser.parse(date_string)
    except ValueError as e:
      logging.error(f"Date parsing error: {e} with string: {date_string}")
      return None

def parse_duration(duration_string):
    """Parses a duration string into seconds."""
    if pd.isna(duration_string):
        return None
    try:
        parts = duration_string.replace("Min", "").replace("Sec", "").strip().split("&")
        total_seconds = 0
        for part in parts:
          part = part.strip()
          if "hour" in part.lower() or "hr" in part.lower():
            hours = int(part.lower().replace("hour", "").replace("hr", "").strip())
            total_seconds += hours * 3600
          elif "min" in part.lower():
              minutes = int(part.lower().replace("min", "").strip())
              total_seconds += minutes * 60
          elif "sec" in part.lower():
              seconds = int(part.lower().replace("sec", "").strip())
              total_seconds += seconds
        return total_seconds
    except ValueError as e:
        print(f"Duration parsing error: {e}")
        return None


class Transform:
    def __init__(self, db_engine):
      self.db_engine = db_engine

    def clean_columns(self, df):
      df.columns = [col.lower().replace(' ', '_') for col in df.columns]
      for col in df.columns:
           if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
      return df
    def transform(self, df):
      pass

class KeylogTransform(Transform):
   def transform(self, df):
       df = df.iloc[2:]
       df.loc[:,'time_dt'] = df['time'].apply(lambda x: parse_datetime(x))
       return df
class SmsMessageTransform(Transform):
   def transform(self, df):
       df = df.iloc[1:]  # skips the header for sms_messages
       df.loc[:,'time_dt'] = df['time'].apply(lambda x: parse_datetime(x))
       return df
class ChatMessageTransform(Transform):
    def transform(self, df):
        df.loc[:,'time_dt'] = df['time'].apply(lambda x: parse_datetime(x))
        return df
class ContactTransform(Transform):
    def transform(self, df):
        df.loc[:,'last_contacted_dt'] = df['last_contacted'].apply(lambda x: parse_datetime(x))
        return df
class CallTransform(Transform):
    def transform(self, df):
        df.loc[:,'time_dt'] = df['time'].apply(lambda x: parse_datetime(x))
        df.loc[:,'duration'] = df['duration_(sec)'].apply(lambda x: parse_duration(x))
        df = df.drop(columns = ['duration_(sec)'])
        return df
class InstalledAppTransform(Transform):
    def transform(self, df):
       df.loc[:,'installed_date'] = df['installed_date'].apply(lambda x: parse_datetime(x))
       return df
class LocationTransform(Transform):
  def transform(self, df):
      return df