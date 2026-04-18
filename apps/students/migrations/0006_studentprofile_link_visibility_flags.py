from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_studentprofile_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentprofile',
            name='show_email_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_resume_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_linkedin_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_github_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_leetcode_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_hackerrank_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_codechef_on_profile',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentprofile',
            name='show_codeforces_on_profile',
            field=models.BooleanField(default=True),
        ),
    ]
