from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random
import string


class BankAccount(models.Model):
    """Bank account model"""

    ACCOUNT_TYPES = [
        ("checking", "Checking Account"),
        ("savings", "Savings Account"),
        ("business", "Business Account"),
        ("premium", "Premium Account"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_type = models.CharField(
        max_length=20, choices=ACCOUNT_TYPES, default="checking"
    )
    account_number = models.CharField(max_length=16, unique=True, blank=True)
    balance = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0.00")
    )
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            self.account_number = self.generate_account_number()

        # Ensure only one primary account per user
        if self.is_primary:
            BankAccount.objects.filter(user=self.user, is_primary=True).exclude(
                id=self.id
            ).update(is_primary=False)

        super().save(*args, **kwargs)

    def generate_account_number(self):
        """Generate unique 16-digit account number"""
        while True:
            account_number = "".join(random.choices(string.digits, k=16))
            if not BankAccount.objects.filter(account_number=account_number).exists():
                return account_number

    def __str__(self):
        return f"{self.get_account_type_display()} - {self.account_number} ({self.user.username})"

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"


class Card(models.Model):
    """Credit/Debit card model"""

    CARD_TYPES = [
        ("debit", "Debit Card"),
        ("credit", "Credit Card"),
        ("prepaid", "Prepaid Card"),
    ]

    CARD_STATUS = [
        ("active", "Active"),
        ("blocked", "Blocked"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cards")
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="cards"
    )
    card_type = models.CharField(max_length=20, choices=CARD_TYPES, default="debit")
    card_number = models.CharField(max_length=16, unique=True, blank=True)
    card_holder_name = models.CharField(max_length=255)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    cvv = models.CharField(max_length=4, blank=True)
    status = models.CharField(max_length=20, choices=CARD_STATUS, default="active")
    is_primary = models.BooleanField(default=False)

    # Credit card specific fields
    credit_limit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    available_credit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.card_number:
            self.card_number = self.generate_card_number()

        if not self.cvv:
            self.cvv = self.generate_cvv()

        if not self.card_holder_name:
            self.card_holder_name = (
                f"{self.user.first_name} {self.user.last_name}".upper()
            )

        # Set available credit for credit cards
        if (
            self.card_type == "credit"
            and self.credit_limit
            and not self.available_credit
        ):
            self.available_credit = self.credit_limit

        # Ensure only one primary card per user
        if self.is_primary:
            Card.objects.filter(user=self.user, is_primary=True).exclude(
                id=self.id
            ).update(is_primary=False)

        super().save(*args, **kwargs)

    def generate_card_number(self):
        """Generate unique 16-digit card number"""
        while True:
            card_number = "".join(random.choices(string.digits, k=16))
            if not Card.objects.filter(card_number=card_number).exists():
                return card_number

    def generate_cvv(self):
        """Generate 3 or 4 digit CVV"""
        return "".join(random.choices(string.digits, k=3))

    def masked_number(self):
        """Return masked card number"""
        if self.card_number:
            return f"****-****-****-{self.card_number[-4:]}"
        return "****-****-****-****"

    def __str__(self):
        return f"{self.get_card_type_display()} - {self.masked_number()} ({self.user.username})"

    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"
