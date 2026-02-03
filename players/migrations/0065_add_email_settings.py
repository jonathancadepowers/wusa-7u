# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0064_remove_event_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('smtp_host', models.CharField(default='smtp.gmail.com', max_length=255)),
                ('smtp_port', models.IntegerField(default=587)),
                ('smtp_username', models.CharField(blank=True, max_length=255, null=True)),
                ('smtp_password', models.CharField(blank=True, help_text='Stored in plain text', max_length=255, null=True)),
                ('smtp_use_tls', models.BooleanField(default=True)),
                ('from_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('reply_to_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('sandbox_mode', models.BooleanField(default=False, help_text='When enabled, all emails are sent to the sandbox email address')),
                ('sandbox_email', models.EmailField(blank=True, help_text='Email address to receive all emails when sandbox mode is enabled', max_length=254, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Email Settings',
                'verbose_name_plural': 'Email Settings',
                'db_table': 'email_settings',
            },
        ),
    ]
