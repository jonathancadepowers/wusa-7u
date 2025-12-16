# Generated manually on 2025-12-16

from django.db import migrations


def add_practice_slots_validation(apps, schema_editor):
    """Add validation code and registry entry for practice slots creation"""
    # Try to create the ValidationCode record, but skip if the table doesn't exist yet
    try:
        ValidationCode = apps.get_model('players', 'ValidationCode')
        ValidationCode.objects.get_or_create(
            code='validation_code_create_practice_slots',
            defaults={
                'value': False,
                'error_message': 'You must create practice slots before accessing this page.'
            }
        )
    except Exception as e:
        # If the table doesn't exist, skip this migration
        # The record will need to be added manually via Django admin
        print(f"Skipping validation code creation: {e}")


def reverse_practice_slots_validation(apps, schema_editor):
    """Remove validation code for practice slots creation"""
    ValidationCode = apps.get_model('players', 'ValidationCode')

    ValidationCode.objects.filter(code='validation_code_create_practice_slots').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0031_alter_validationcode_value'),
    ]

    operations = [
        migrations.RunPython(add_practice_slots_validation, reverse_practice_slots_validation),
    ]
