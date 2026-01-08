from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0043_add_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('bootstrap_icon_id', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'event_types',
                'verbose_name': 'Event Type',
                'verbose_name_plural': 'Event Types',
                'ordering': ['name'],
            },
        ),
    ]
