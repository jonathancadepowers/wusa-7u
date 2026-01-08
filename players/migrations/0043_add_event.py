from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0042_add_board_member'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('timestamp', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'events',
                'verbose_name': 'Event',
                'verbose_name_plural': 'Events',
                'ordering': ['-timestamp'],
            },
        ),
    ]
