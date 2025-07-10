from django.db import models


class User(models.AbstractBaseUser):
    username = None
    email = models.EmailField(unique=True)
    is_author = models.BooleanField(default=False)
    is_editor = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"

    def __str__(self):
        return self.email
