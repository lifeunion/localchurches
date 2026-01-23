-- Fix missing content_type_id column in wagtailcore_workflowstate table
-- Run this NOW in Render PostgreSQL database to fix the admin console issue

-- Add missing column
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS content_type_id INTEGER NULL;

-- Verify column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_workflowstate' 
AND column_name = 'content_type_id';
