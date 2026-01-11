from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0049_change_attended_try_out_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='draft',
            name='final_round_picks',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
