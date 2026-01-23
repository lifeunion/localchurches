-- Fix missing file_size column in wagtaildocs_document table for Wagtail 6.4
-- Run this NOW in Render PostgreSQL database to fix the admin console issue

-- Add missing file_size column
ALTER TABLE wagtaildocs_document 
ADD COLUMN IF NOT EXISTS file_size INTEGER NULL;

-- Verify column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtaildocs_document' 
AND column_name = 'file_size';
