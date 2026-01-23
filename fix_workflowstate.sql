-- Fix missing columns in wagtailcore_workflowstate table for Wagtail 6.4
-- Run this NOW in Render PostgreSQL database to fix the admin console issue

-- Add missing content_type_id column
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS content_type_id INTEGER NULL;

-- Add missing base_content_type_id column (Wagtail 6.4)
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS base_content_type_id INTEGER NULL;

-- Add missing object_id column (generic foreign key)
ALTER TABLE wagtailcore_workflowstate 
ADD COLUMN IF NOT EXISTS object_id INTEGER NULL;

-- Verify columns were added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailcore_workflowstate' 
AND column_name IN ('content_type_id', 'base_content_type_id', 'object_id')
ORDER BY column_name;
