from django.contrib.auth.models import User

if not User.objects.filter(username="admin").exists():
    User.objects.create_superuser(
        username="admin",
        email="admin@test.com",
        password="admin12345"
    )
