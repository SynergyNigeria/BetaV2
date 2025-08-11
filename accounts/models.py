from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random
import string


class UserProfile(models.Model):
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=10, blank=True, null=True)
    """Extended user profile model"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=12, unique=True, blank=True)
    security_question = models.TextField(blank=True, null=True)
    security_answer = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(blank=True, null=True)
    occid_pin = models.CharField(
        max_length=6,
        unique=True,
        blank=True,
        null=True,
        help_text="6-digit OCCID PIN for secure transactions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()

        if not self.occid_pin:
            self.occid_pin = self.generate_occid_pin()

        super().save(*args, **kwargs)

    def generate_account_number(self):
        """Generate unique 12-digit account number"""
        while True:
            account_number = "".join(random.choices(string.digits, k=12))
            if not UserProfile.objects.filter(account_number=account_number).exists():
                return account_number

    def generate_occid_pin(self):
        """Generate unique 6-digit OCCID PIN"""
        while True:
            occid_pin = "".join(random.choices(string.digits, k=6))
            if not UserProfile.objects.filter(occid_pin=occid_pin).exists():
                return occid_pin

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
