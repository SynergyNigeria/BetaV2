from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from banking.models import BankAccount
from decimal import Decimal
import random
import string


class Deposit(models.Model):
    DEPOSIT_METHODS = [
        ("usdt", "USDT"),
        ("giftcard", "Gift Card"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="deposits")
    method = models.CharField(max_length=20, choices=DEPOSIT_METHODS)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    reference_number = models.CharField(max_length=30, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    # For gift card deposits
    card_type = models.CharField(max_length=50, blank=True, null=True)
    card_code = models.CharField(max_length=100, blank=True, null=True)
    card_proof = models.ImageField(upload_to="deposit_proofs/", blank=True, null=True)

    # For USDT deposits
    tx_hash = models.CharField(max_length=100, blank=True, null=True)
    usdt_address = models.CharField(max_length=100, blank=True, null=True)

    # Verification
    verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_deposits",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        super().save(*args, **kwargs)

    def generate_reference_number(self):
        while True:
            ref_num = (
                "DEP-"
                + timezone.now().strftime("%y%m%d-")
                + "".join(random.choices(string.digits, k=3))
            )
            if not Deposit.objects.filter(reference_number=ref_num).exists():
                return ref_num

    def __str__(self):
        return f"{self.user.username} - {self.method} - ${self.amount}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Deposit"
        verbose_name_plural = "Deposits"


class Transaction(models.Model):
    """Model for all bank transactions"""

    TRANSACTION_TYPES = [
        ("transfer_internal", "BetaBank Transfer"),
        ("transfer_external", "External Bank Transfer"),
        ("deposit", "Deposit"),
        ("withdrawal", "Withdrawal"),
        ("fee", "Service Fee"),
        ("investment", "Investment"),
        ("investment_withdrawal", "Investment Withdrawal"),
    ]

    transaction_id = models.CharField(max_length=20, unique=True, blank=True)
    reference_number = models.CharField(max_length=20, unique=True, blank=True)
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPES)
    status = models.CharField(
        max_length=15,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
        ],
        default="pending",
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    description = models.TextField(blank=True, null=True)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transactions"
    )
    from_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name="outgoing_transactions"
    )
    to_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name="incoming_transactions",
        blank=True,
        null=True,
    )

    recipient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_transactions",
    )
    recipient_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_account_number = models.CharField(max_length=50, blank=True, null=True)
    recipient_account_holder = models.CharField(max_length=255, blank=True, null=True)
    recipient_bank_name = models.CharField(max_length=255, blank=True, null=True)
    routing_swift_code = models.CharField(max_length=50, blank=True, null=True)

    transfer_type = models.CharField(
        max_length=20,
        choices=[
            ("domestic", "Domestic Transfer"),
            ("international", "International Transfer"),
        ],
        blank=True,
        null=True,
    )
    transfer_purpose = models.CharField(max_length=255, blank=True, null=True)

    occid_verified = models.BooleanField(default=False)
    occid_verified_at = models.DateTimeField(blank=True, null=True)

    deposit = models.ForeignKey(
        "Deposit",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        if not self.reference_number:
            self.reference_number = self.generate_reference_number()
        if (
            self.transaction_type == "transfer_internal"
            and self.recipient_user
            and not self.recipient_name
        ):
            self.recipient_name = (
                self.recipient_user.get_full_name() or self.recipient_user.username
            )
        super().save(*args, **kwargs)

    def generate_transaction_id(self):
        while True:
            trans_id = "TXN" + "".join(random.choices(string.digits, k=10))
            if not Transaction.objects.filter(transaction_id=trans_id).exists():
                return trans_id

    def generate_reference_number(self):
        while True:
            ref_num = "REF" + "".join(
                random.choices(string.ascii_uppercase + string.digits, k=10)
            )
            if not Transaction.objects.filter(reference_number=ref_num).exists():
                return ref_num

    def get_total_amount(self):
        return self.amount + self.fee

    def __str__(self):
        return f"{self.transaction_id} - {self.get_transaction_type_display()} - ${self.amount}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"


class TransferSession(models.Model):
    """Model to store transfer session data for multi-step process"""

    session_id = models.UUIDField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Transfer data
    transfer_type = models.CharField(max_length=20)  # 'betabank' or 'otherbank'
    from_account_id = models.IntegerField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    # BetaBank transfer fields
    recipient_identifier = models.CharField(max_length=255, blank=True, null=True)

    # External bank transfer fields
    bank_transfer_type = models.CharField(max_length=20, blank=True, null=True)
    recipient_bank_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_account_number = models.CharField(max_length=50, blank=True, null=True)
    recipient_account_holder = models.CharField(max_length=255, blank=True, null=True)
    routing_swift_code = models.CharField(max_length=50, blank=True, null=True)
    transfer_purpose = models.CharField(max_length=255, blank=True, null=True)

    # Session management
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Sessions expire after 30 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=30)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Check if session has expired"""
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Transfer Session {self.session_id} - {self.user.username}"

    class Meta:
        verbose_name = "Transfer Session"
        verbose_name_plural = "Transfer Sessions"
