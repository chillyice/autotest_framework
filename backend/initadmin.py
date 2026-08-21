# 启动一次开发用的 Django superuser 创建脚本
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autotest_platform.settings")
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

if User.objects.filter(username=username).exists():
    print(f"[initadmin] user '{username}' already exists, skip")
else:
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"[initadmin] superuser '{username}' created")
