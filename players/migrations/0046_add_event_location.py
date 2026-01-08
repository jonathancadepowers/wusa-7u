from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0045_event_replace_type_with_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='location',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
