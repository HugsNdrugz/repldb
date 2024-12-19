CREATE TABLE IF NOT EXISTS keylogs (
    application TEXT,
    time TEXT,
    time_dt DATETIME,
    text TEXT,
    package_id TEXT,
    UNIQUE(application, time, text)
);

CREATE INDEX IF NOT EXISTS idx_keylogs_time_dt ON keylogs(time_dt);

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

CREATE INDEX IF NOT EXISTS idx_sms_messages_time_dt ON sms_messages(time_dt);
CREATE INDEX IF NOT EXISTS idx_sms_messages_contact_id ON sms_messages(contact_id);

CREATE TABLE IF NOT EXISTS chat_messages (
    messenger TEXT,
    time TEXT,
    time_dt DATETIME,
    sender TEXT,
    text TEXT,
    contact_id INTEGER,
    UNIQUE(messenger, time, sender, text)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_time_dt ON chat_messages(time_dt);
CREATE INDEX IF NOT EXISTS idx_chat_messages_contact_id ON chat_messages(contact_id);



CREATE TABLE IF NOT EXISTS contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone_number TEXT,
    email_id TEXT,
    last_contacted TEXT,
    last_contacted_dt DATETIME,
    UNIQUE(name, phone_number, email_id)
);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);


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

CREATE INDEX IF NOT EXISTS idx_calls_time_dt ON calls(time_dt);
CREATE INDEX IF NOT EXISTS idx_calls_contact_id ON calls(contact_id);


CREATE TABLE IF NOT EXISTS installedapps (
    application_name TEXT,
    package_name TEXT,
    installed_date DATETIME,
    UNIQUE(application_name, package_name)
);
CREATE INDEX IF NOT EXISTS idx_installedapps_application_name ON installedapps(application_name);


CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_text TEXT UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_locations_location_text ON locations(location_text);