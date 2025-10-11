from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import uuid


class Loan(models.Model):
    """Model for loan applications and management"""

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("disbursed", "Disbursed"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    LOAN_TYPES = [
        ("personal", "Personal Loan"),
        ("auto", "Auto Loan"),
        ("business", "Business Loan"),
        ("education", "Education Loan"),
        ("mortgage", "Home Mortgage"),
        ("quick", "Quick Loan"),
    ]

    # Basic Information
    loan_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES, default="quick")

    # Financial Details
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2)
    amount_approved = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00"),
        help_text="Interest rate as percentage",
    )

    # Status and Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    purpose = models.TextField(blank=True, null=True, help_text="Purpose of the loan")

    # Dates
    application_date = models.DateTimeField(auto_now_add=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    disbursement_date = models.DateTimeField(null=True, blank=True)

    # Admin Review
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_loans",
    )
    admin_notes = models.TextField(
        blank=True, null=True, help_text="Internal admin notes"
    )
    rejection_reason = models.TextField(
        blank=True, null=True, help_text="Reason for rejection"
    )

    # Bank Account Integration
    disbursement_account = models.ForeignKey(
        "banking.BankAccount",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Account where loan amount will be deposited",
    )

    # Reference and Tracking
    reference_number = models.CharField(max_length=20, unique=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"LN-{self.loan_id.hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def days_since_application(self):
        """Get number of days since loan application"""
        delta = timezone.now() - self.application_date
        return delta.days

    @property
    def is_pending(self):
        """Check if loan is still pending"""
        return self.status == "pending"

    @property
    def is_approved(self):
        """Check if loan is approved"""
        return self.status in ["approved", "disbursed", "active"]

    def approve_loan(self, admin_user, approved_amount=None, notes=None):
        """Approve the loan application"""
        self.status = "approved"
        self.reviewed_by = admin_user
        self.review_date = timezone.now()
        self.approval_date = timezone.now()
        self.amount_approved = approved_amount or self.amount_requested
        if notes:
            self.admin_notes = notes
        self.save()

    def reject_loan(self, admin_user, reason=None, notes=None):
        """Reject the loan application"""
        self.status = "rejected"
        self.reviewed_by = admin_user
        self.review_date = timezone.now()
        if reason:
            self.rejection_reason = reason
        if notes:
            self.admin_notes = notes
        self.save()

    def disburse_loan(self, admin_user=None):
        """Mark loan as disbursed (money added to account)"""
        self.status = "disbursed"
        self.disbursement_date = timezone.now()
        if admin_user:
            self.reviewed_by = admin_user
        self.save()

    def __str__(self):
        return f"Loan {self.reference_number} - {self.user.username} - ${self.amount_requested}"

    class Meta:
        ordering = ["-application_date"]
        verbose_name = "Loan Application"
        verbose_name_plural = "Loan Applications"


class LoanStatusUpdate(models.Model):
    """Track loan status changes for notifications"""

    loan = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name="status_updates"
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan.reference_number}: {self.old_status} → {self.new_status}"

    class Meta:
        ordering = ["-created_at"]
