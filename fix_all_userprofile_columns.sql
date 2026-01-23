-- Fix all missing Wagtail 6.4 UserProfile columns
-- Run this in Render PostgreSQL database (via psql or Render dashboard)
-- Based on wagtail/users/models.py UserProfile model

-- Add all missing columns if they don't exist
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT TRUE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS rejected_notifications BOOLEAN DEFAULT TRUE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS current_time_zone VARCHAR(40) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS avatar VARCHAR(100) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS dismissibles JSONB DEFAULT '{}'::jsonb NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS theme VARCHAR(40) DEFAULT 'system' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS contrast VARCHAR(40) DEFAULT 'system' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS density VARCHAR(40) DEFAULT 'default' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS keyboard_shortcuts BOOLEAN DEFAULT TRUE NOT NULL;

-- Verify all columns were added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name IN (
    'updated_comments_notifications', 
    'rejected_notifications', 
    'current_time_zone', 
    'preferred_language',
    'avatar',
    'dismissibles',
    'theme',
    'contrast',
    'density',
    'keyboard_shortcuts'
)
ORDER BY column_name;
