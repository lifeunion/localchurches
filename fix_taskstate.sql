-- Fix missing revision_id column in wagtailcore_taskstate table for Wagtail 6.4
-- Run this NOW in Render PostgreSQL database to fix the admin console issue

-- Add missing revision_id column
ALTER TABLE wagtailcore_taskstate 
ADD COLUMN IF NOT EXISTS revision_id INTEGER NULL;

-- Verify column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_taskstate' 
AND column_name = 'revision_id';
