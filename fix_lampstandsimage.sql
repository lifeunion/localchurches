-- Fix missing columns in lampstands_lampstandsimage table for Wagtail 6.4 compatibility
-- Run this script if you see: column lampstands_lampstandsimage.description does not exist

-- Add description column (from Wagtail AbstractImage)
-- Check if column exists first to avoid errors on re-run
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'lampstands_lampstandsimage'
        AND column_name = 'description'
    ) THEN
        ALTER TABLE lampstands_lampstandsimage 
        ADD COLUMN description TEXT NULL;
        
        RAISE NOTICE 'Added description column to lampstands_lampstandsimage';
    ELSE
        RAISE NOTICE 'Column description already exists in lampstands_lampstandsimage';
    END IF;
END $$;

-- Verify the column was added
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'lampstands_lampstandsimage'
AND column_name = 'description';
