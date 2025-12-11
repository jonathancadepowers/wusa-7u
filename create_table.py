import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wusa_7u.settings')
django.setup()

from django.db import connection

# Create the table using raw SQL
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS division_validation_registry (
            id SERIAL PRIMARY KEY,
            page TEXT NOT NULL,
            required_validations TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
    """)

print("Table 'division_validation_registry' created successfully!")

# Verify it was created
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'division_validation_registry'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print("\nTable structure:")
    for col_name, data_type in columns:
        print(f"  - {col_name}: {data_type}")
