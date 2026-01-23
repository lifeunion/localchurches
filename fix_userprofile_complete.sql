-- Complete fix for ALL missing Wagtail 6.4 UserProfile columns
-- Run this NOW in Render PostgreSQL database to fix the admin console issue
-- Based on wagtail/users/models.py UserProfile model

-- Notification columns
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT TRUE NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS rejected_notifications BOOLEAN DEFAULT TRUE NOT NULL;

-- Language and timezone
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS current_time_zone VARCHAR(40) DEFAULT '' NOT NULL;

ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(10) DEFAULT '' NOT NULL;

-- Avatar (ImageField - stores file path)
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS avatar VARCHAR(100) DEFAULT '' NOT NULL;

-- UI preferences
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

-- Fix wagtailcore_workflowstate table
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS content_type_id INTEGER NULL;

-- Verify all columns were added
SELECT column_name, data_type, column_default 
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

-- Verify workflowstate column
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_workflowstate' 
AND column_name = 'content_type_id';
