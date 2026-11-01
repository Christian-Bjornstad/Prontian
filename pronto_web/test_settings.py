"""Isolated defaults used only by pytest-django tests."""

import os

os.environ.setdefault("PRONTO_DJANGO_SECRET_KEY", "synthetic-test-only-not-for-deployment")

from . import settings as base

globals().update({name: value for name, value in vars(base).items() if name.isupper()})

# Password policy is tested separately; hashing speed must not dominate request
# tests. This setting is confined to tests and is never used by the launchers.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
