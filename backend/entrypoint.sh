#!/bin/sh
set -e

echo "⏳ Waiting for database..."
while ! nc -z db 5432; do
    sleep 1
done
echo "✅ Database ready"

echo "⏳ Waiting for Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "✅ Redis ready"

echo "🔄 Running migrations..."
python manage.py makemigrations --noinput 2>/dev/null || true
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "👤 Creating superuser (if not exists)..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@ibs.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin@12345')
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        password=password,
        full_name='Admin User',
        phone='01700000000',
        role='ADMIN',
        status='ACTIVE',
    )
    print(f"✅ Superuser created: {email}")
else:
    print(f"ℹ️  Superuser already exists: {email}")
EOF

echo "🚀 Starting Django..."
exec "$@"