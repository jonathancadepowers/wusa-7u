# Generated manually on 2025-12-16

from django.db import migrations


def add_practice_slots_validation(apps, schema_editor):
    """Add validation code and registry entry for practice slots creation"""
    ValidationCode = apps.get_model('players', 'ValidationCode')
    DivisionValidationRegistry = apps.get_model('players', 'DivisionValidationRegistry')

    # Create ValidationCode record
    ValidationCode.objects.get_or_create(
        code='validation_code_create_practice_slots',
        defaults={
            'value': False,
            'error_message': 'You must create practice slots before accessing this page.'
        }
    )

    # Create DivisionValidationRegistry record
    DivisionValidationRegistry.objects.get_or_create(
        page='/practice_slots/',
        defaults={
            'validation_1': '',
            'validation_2': '',
            'validation_3': '',
            'validation_4': '',
            'validation_5': ''
        }
    )


def reverse_practice_slots_validation(apps, schema_editor):
    """Remove validation code and registry entry for practice slots creation"""
    ValidationCode = apps.get_model('players', 'ValidationCode')
    DivisionValidationRegistry = apps.get_model('players', 'DivisionValidationRegistry')

    ValidationCode.objects.filter(code='validation_code_create_practice_slots').delete()
    DivisionValidationRegistry.objects.filter(page='/practice_slots/').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0031_alter_validationcode_value'),
    ]

    operations = [
        migrations.RunPython(add_practice_slots_validation, reverse_practice_slots_validation),
    ]
