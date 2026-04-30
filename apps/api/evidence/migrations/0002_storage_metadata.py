from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("evidence", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="evidenceitem",
            name="storage_backend",
            field=models.CharField(
                choices=[("LOCAL", "Local"), ("AZURE_BLOB", "Azure Blob")],
                default="LOCAL",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="evidenceitem",
            name="storage_reference",
            field=models.CharField(blank=True, max_length=512),
        ),
    ]
