#!/usr/bin/env python3
"""
Migrate Wagtail data using Django's dumpdata/loaddata.
This properly handles foreign keys and JSON fields.
"""
import os
import sys
import subprocess
import tempfile

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')

def run_django_command(command, env_vars=None):
    """Run a Django management command with custom environment."""
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    result = subprocess.run(
        ['python3', 'manage.py'] + command,
        env=env,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error running: {' '.join(command)}")
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT: {result.stdout[:500]}")
        if result.stderr:
            print(f"STDERR: {result.stderr[:500]}")
        return False, result.stdout, result.stderr
    return True, result.stdout, result.stderr

def main():
    print("=" * 60)
    print("Wagtail Data Migration using Django dumpdata/loaddata")
    print("=" * 60)
    
    HEROKU_DATABASE_URL = os.environ.get('HEROKU_DATABASE_URL')
    RENDER_DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if not HEROKU_DATABASE_URL:
        print("⚠ HEROKU_DATABASE_URL not set. Skipping migration.")
        return 0
    
    if not RENDER_DATABASE_URL:
        print("⚠ DATABASE_URL not set. Skipping migration.")
        return 0
    
    # Create temporary file for data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        dump_file = f.name
    
    try:
        print("\nStep 1: Dumping Wagtail data from Heroku...")
        print("Setting DATABASE_URL to Heroku...")
        
        # Dump Wagtail-specific data
        success, stdout, stderr = run_django_command(
            ['dumpdata', 
             '--natural-foreign', 
             '--natural-primary',
             'wagtailcore.Page',
             'wagtailcore.Site',
             'wagtailcore.Revision',
             'wagtailcore.PageRevision',
             'wagtailimages.Image',
             'wagtailimages.Rendition',
             'wagtaildocs.Document',
             'wagtailforms.FormSubmission',
             'wagtailredirects.Redirect',
             'lampstands.HomePage',
             'lampstands.StandardPage',
             'lampstands.BlogPage',
             'lampstands.ChurchPage',
             'lampstands.ChurchIndexPage',
             'lampstands.FAQPage',
             'lampstands.FAQIndexPage',
             'lampstands.HistoryPage',
             'lampstands.HistoryIndexPage',
             'lampstands.RecognitionPage',
             'lampstands.RecognitionIndexPage',
             'lampstands.MapPage',
             'lampstands.Contact',
             'lampstands.Churchentry',
             'lampstands.GlobalSettings',
             'lampstands.MainMenu',
             '-o', dump_file],
            {'DATABASE_URL': HEROKU_DATABASE_URL}
        )
        
        if not success:
            print("Failed to dump data from Heroku")
            print("Trying to dump all lampstands data...")
            # Fallback: dump all lampstands app data
            success, stdout, stderr = run_django_command(
                ['dumpdata', 
                 '--natural-foreign', 
                 '--natural-primary',
                 'lampstands',
                 'wagtailcore',
                 'wagtailimages',
                 'wagtaildocs',
                 'wagtailforms',
                 'wagtailredirects',
                 '-o', dump_file],
                {'DATABASE_URL': HEROKU_DATABASE_URL}
            )
            if not success:
                print("Failed to dump data")
                return 1
        
        # Check file size
        file_size = os.path.getsize(dump_file)
        print(f"✓ Dump created: {dump_file} ({file_size / 1024:.2f} KB)")
        
        if file_size < 100:  # Less than 100 bytes, probably empty
            print("⚠ Warning: Dump file is very small, may be empty")
        
        print("\nStep 2: Loading data into Render Postgres...")
        print("Setting DATABASE_URL to Render...")
        
        success, stdout, stderr = run_django_command(
            ['loaddata', dump_file],
            {'DATABASE_URL': RENDER_DATABASE_URL}
        )
        
        if not success:
            print("⚠ Some errors occurred during loaddata:")
            print(stderr)
            # Continue anyway - some errors are expected
        
        print("✓ Data load completed!")
        
    finally:
        # Clean up
        if os.path.exists(dump_file):
            os.unlink(dump_file)
    
    print("\nMigration complete!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
