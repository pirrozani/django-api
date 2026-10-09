from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


# Hash any password stored in plain text by the API before #3
def hash_plain_text_passwords(apps, schema_editor):
    User = apps.get_model('api', 'User')
    for user in User.objects.only('id', 'password'):
        try:
            identify_hasher(user.password)
        except ValueError:
            user.password = make_password(user.password)
            user.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_blog'),
    ]

    operations = [
        migrations.RunPython(hash_plain_text_passwords, migrations.RunPython.noop),
    ]
