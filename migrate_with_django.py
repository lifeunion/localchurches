#!/usr/bin/env python3
"""
Database migration using Django's dumpdata/loaddata commands.
This works regardless of Postgres version differences.
"""
import os
import sys
import subprocess
import json
import tempfile

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')

# Connection strings - set via environment (no hardcoded secrets)
HEROKU_DATABASE_URL = os.environ.get('HEROKU_DATABASE_URL')
RENDER_DATABASE_URL = os.environ.get('RENDER_DATABASE_URL')

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
        print(result.stderr)
        return False
    return True

def main():
    print("Database Migration using Django dumpdata/loaddata")
    print("=" * 60)
    
    if not HEROKU_DATABASE_URL:
        print("Error: HEROKU_DATABASE_URL not set. export HEROKU_DATABASE_URL='postgres://...'")
        sys.exit(1)
    if not RENDER_DATABASE_URL:
        print("Error: RENDER_DATABASE_URL not set. export RENDER_DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    # Create temporary file for data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        dump_file = f.name
    
    try:
        print("\nStep 1: Dumping data from Heroku Postgres...")
        print("Setting DATABASE_URL to Heroku...")
        
        if not run_django_command(
            ['dumpdata', '--natural-foreign', '--natural-primary', '--exclude', 'contenttypes', '--exclude', 'auth.permission', '--exclude', 'admin.logentry', '-o', dump_file],
            {'DATABASE_URL': HEROKU_DATABASE_URL}
        ):
            print("Failed to dump data from Heroku")
            sys.exit(1)
        
        # Check file size
        file_size = os.path.getsize(dump_file)
        print(f"✓ Dump created: {dump_file} ({file_size / 1024:.2f} KB)")
        
        print("\nStep 2: Loading data into Render Postgres...")
        print("Setting DATABASE_URL to Render...")
        
        if not run_django_command(
            ['loaddata', dump_file],
            {'DATABASE_URL': RENDER_DATABASE_URL}
        ):
            print("Failed to load data into Render")
            print("Note: Some errors are normal if tables don't exist yet")
            print("You may need to run migrations first on Render")
            sys.exit(1)
        
        print("✓ Data loaded successfully!")
        
    finally:
        # Clean up
        if os.path.exists(dump_file):
            os.unlink(dump_file)
    
    print("\nMigration complete!")
    print("\nNext steps:")
    print("1. Link the database to your web service in Render dashboard")
    print("2. Run migrations: python manage.py migrate")
    print("3. Deploy your app")

if __name__ == '__main__':
    main()
