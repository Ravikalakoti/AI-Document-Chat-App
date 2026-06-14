from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User

class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_subscribed = models.BooleanField(default=False)
    subscribed_at = models.DateTimeField(null=True, blank=True)
    plan_name = models.CharField(max_length=50, default="Free")

    expires_at = models.DateTimeField(null=True, blank=True)

    def is_active(self):
        if not self.is_subscribed:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"{self.user.username} - {self.plan_name}"