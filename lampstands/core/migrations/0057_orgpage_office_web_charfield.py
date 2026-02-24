# Remove URL validation from Office web and Office web 2 so notes are allowed.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0056_churchpage_consented_brother_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="orgpage",
            name="office_web",
            field=models.CharField(blank=True, help_text='URL or note (e.g. "See main site")', max_length=500),
        ),
        migrations.AlterField(
            model_name="orgpage",
            name="office_web_2",
            field=models.CharField(blank=True, help_text='URL or note (e.g. "See main site")', max_length=500),
        ),
    ]
