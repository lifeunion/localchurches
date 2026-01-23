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

-- Fix wagtailcore_workflowstate table (Wagtail 6.4)
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS content_type_id INTEGER NULL;

ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS base_content_type_id INTEGER NULL;

ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS object_id INTEGER NULL;

-- Fix wagtailcore_taskstate table (Wagtail 6.4)
ALTER TABLE wagtailcore_taskstate 
ADD COLUMN IF NOT EXISTS revision_id INTEGER NULL;

-- Fix wagtailcore_revision table (Wagtail 6.4)
ALTER TABLE wagtailcore_revision 
ADD COLUMN IF NOT EXISTS object_str TEXT NULL;

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

-- Verify workflowstate columns
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_workflowstate' 
AND column_name IN ('content_type_id', 'base_content_type_id', 'object_id')
ORDER BY column_name;

-- Verify taskstate column
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_taskstate' 
AND column_name = 'revision_id';

-- Verify revision column
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_revision' 
AND column_name = 'object_str';
