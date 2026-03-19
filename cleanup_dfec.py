import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portalstae.settings')
django.setup()

def clean():
    with connection.cursor() as cursor:
        # Find all DFEC tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'dfec_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables to drop: {tables}")
        
        # Drop them
        for table in tables:
            print(f"Dropping {table}...")
            cursor.execute(f"DROP TABLE {table}")
            
        # Clear migrations
        print("Clearing django_migrations for dfec...")
        cursor.execute("DELETE FROM django_migrations WHERE app='dfec'")
        
    print("Cleanup complete!")

if __name__ == '__main__':
    clean()
