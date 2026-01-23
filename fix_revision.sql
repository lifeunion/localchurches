-- Fix missing object_str column in wagtailcore_revision table for Wagtail 6.4
-- Run this NOW in Render PostgreSQL database to fix the admin console issue

-- Add missing object_str column
ALTER TABLE wagtailcore_revision 
ADD COLUMN IF NOT EXISTS object_str TEXT NULL;

-- Verify column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_revision' 
AND column_name = 'object_str';
