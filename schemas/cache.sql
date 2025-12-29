-- Cache file schema
-- Ignacio version: 0.1.0

-- Guild-specific settings
CREATE TABLE IF NOT EXISTS settings (
    guild INTEGER NOT NULL PRIMARY KEY, -- Unique guild ID
    language TINYTEXT -- Language code
);

-- Tracked text channels
CREATE TABLE IF NOT EXISTS tracked (
    id INTEGER NOT NULL PRIMARY KEY, -- Unique text channel ID
    guild INTEGER -- Unique guild ID
);