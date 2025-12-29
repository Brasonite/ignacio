-- Recording file schema
-- Ignacio version: 0.1.0

-- Recording metadata.
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Guarantees only one metadata record can exist
    guild INTEGER NOT NULL, -- The ID of the guild where this recording was made
    length FLOAT, -- Recording length, in seconds
    audio_start FLOAT -- Timestamp of when the first audio track starts
);

-- User metadata
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY, -- Unique user ID
    name TINYTEXT NOT NULL, -- Username
    display_name TINYTEXT NOT NULL, -- Display name
    avatar MEDIUMBLOB NOT NULL, -- Avatar bytes
    avatar_type TINYTEXT -- Avatar MIME type
);

-- Audio tracks
CREATE TABLE audio (
    user INTEGER NOT NULL PRIMARY KEY, -- User ID
    mime TINYTEXT NOT NULL, -- Audio MIME type
    data MEDIUMBLOB NOT NULL -- Audio bytes
);

-- Voice channel events (joining/leaving)
CREATE TABLE events (
    offset FLOAT NOT NULL, -- Timestamp relative to the recording's beginning
    user INTEGER NOT NULL, -- User ID
    type INTEGER NOT NULL -- Event type (JOIN = 0, LEAVE = 1)
);

-- Text channel metadata
CREATE TABLE channels (
    id INTEGER NOT NULL PRIMARY KEY, -- Unique channel ID
    name TINYTEXT NOT NULL
);

-- Text messages
CREATE TABLE messages (
    offset FLOAT NOT NULL, -- Timestamp relative to the recording's beginning
    user INTEGER NOT NULL, -- User ID
    channel INTEGER NOT NULL, -- Channel ID
    text TEXT, -- Message content
    attachments TEXT -- Sequence of attachment UUIDs
);

-- Text message attachments
CREATE TABLE attachments (
    id TEXT NOT NULL PRIMARY KEY, -- Attachment UUID
    mime TINYTEXT, -- Data MIME type
    data MEDIUMBLOB NOT NULL -- Data bytes
);