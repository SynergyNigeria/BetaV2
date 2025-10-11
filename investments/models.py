from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


class InvestmentPlan(models.Model):
    """Investment plan templates that users can choose from"""

    PLAN_TYPES = [
        ("basic", "Basic Plan"),
        ("premium", "Premium Plan"),
        ("gold", "Gold Plan"),
        ("platinum", "Platinum Plan"),
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default="basic")
    description = models.TextField()
    minimum_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("100.00")
    )
    maximum_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Interest rate as percentage (e.g., 15.50)",
    )
    duration_days = models.IntegerField(
        default=14, help_text="Investment duration in days"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.interest_rate}% for {self.duration_days} days"

    def calculate_returns(self, principal_amount):
        """Calculate total returns for a given principal amount"""
        interest = (principal_amount * self.interest_rate) / Decimal("100")
        return principal_amount + interest

    class Meta:
        ordering = ["plan_type", "minimum_amount"]


class Investment(models.Model):
    """User investments"""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("matured", "Matured"),
        ("withdrawn", "Withdrawn"),
        ("cancelled", "Cancelled"),
    ]

    investment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="investments")
    plan = models.ForeignKey(
        InvestmentPlan, on_delete=models.CASCADE, related_name="investments"
    )
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    expected_returns = models.DecimalField(max_digits=15, decimal_places=2)
    actual_returns = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Dates
    start_date = models.DateTimeField(default=timezone.now)
    maturity_date = models.DateTimeField()
    withdrawal_date = models.DateTimeField(null=True, blank=True)

    # Transaction tracking
    from_account = models.ForeignKey(
        "banking.BankAccount", on_delete=models.CASCADE, related_name="investments_made"
    )
    transaction_reference = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.maturity_date:
            self.maturity_date = self.start_date + timezone.timedelta(
                days=self.plan.duration_days
            )
        if not self.expected_returns:
            self.expected_returns = self.plan.calculate_returns(self.principal_amount)
        if not self.transaction_reference:
            self.transaction_reference = f"INV-{self.investment_id.hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_matured(self):
        """Check if investment has matured"""
        return timezone.now() >= self.maturity_date

    @property
    def days_remaining(self):
        """Get remaining days until maturity"""
        if self.is_matured:
            return 0
        delta = self.maturity_date - timezone.now()
        return max(0, delta.days)

    @property
    def days_invested(self):
        """Get number of days since investment started"""
        delta = timezone.now() - self.start_date
        return delta.days

    @property
    def progress_percentage(self):
        """Get investment progress as percentage"""
        total_days = self.plan.duration_days
        days_passed = min(self.days_invested, total_days)
        return (days_passed / total_days) * 100

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} - ${self.principal_amount}"

    class Meta:
        ordering = ["-start_date"]


class InvestmentTransaction(models.Model):
    """Track all investment-related transactions"""

    TRANSACTION_TYPES = [
        ("investment", "New Investment"),
        ("withdrawal", "Withdrawal"),
        ("return", "Returns Payment"),
    ]

    investment = models.ForeignKey(
        Investment, on_delete=models.CASCADE, related_name="transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    reference = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"INVTXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} - {self.investment.user.username} - ${self.amount}"

    class Meta:
        ordering = ["-created_at"]
