-- SQL script to fix missing updated_comments_notifications column
-- Run this in Render's PostgreSQL database (via psql or Render dashboard)

-- Add the missing column if it doesn't exist
ALTER TABLE wagtailusers_userprofile 
ADD COLUMN IF NOT EXISTS updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;

-- Verify the column was added
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'wagtailusers_userprofile' 
AND column_name = 'updated_comments_notifications';
