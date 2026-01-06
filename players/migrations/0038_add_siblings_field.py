# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0037_add_sandbox_test_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='siblings',
            field=models.ManyToManyField(blank=True, to='players.Player'),
        ),
    ]
