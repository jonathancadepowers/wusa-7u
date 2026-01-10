from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0048_add_eventtype_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='player',
            name='attended_try_out',
            field=models.BooleanField(default=False),
        ),
    ]
