# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0039_add_requests_separate_team_from_sibling'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiblingRanking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ranking', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('manager', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sibling_rankings', to='players.manager')),
            ],
            options={
                'db_table': 'sibling_rankings',
            },
        ),
    ]
