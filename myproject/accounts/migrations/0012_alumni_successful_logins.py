from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_job"),
    ]

    operations = [
        migrations.AddField(
            model_name="alumni",
            name="successful_logins",
            field=models.PositiveIntegerField(default=0),
        ),
    ]