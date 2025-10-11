from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import Loan, LoanStatusUpdate
from banking.models import BankAccount
from transactions.models import Transaction
from notifications.models import Notification


class LoanStatusUpdateInline(admin.TabularInline):
    """Inline admin for Loan Status Updates"""

    model = LoanStatusUpdate
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("old_status", "new_status", "updated_by", "notes", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin interface for Loan Applications"""

    list_display = (
        "reference_number",
        "user",
        "loan_type",
        "amount_requested",
        "amount_approved",
        "status_badge",
        "application_date",
        "days_since_application",
    )
    list_filter = ("status", "loan_type", "application_date", "approval_date")
    search_fields = ("reference_number", "user__username", "user__email", "loan_id")
    readonly_fields = (
        "loan_id",
        "reference_number",
        "application_date",
        "days_since_application",
        "created_at",
        "updated_at",
    )
    inlines = [LoanStatusUpdateInline]

    fieldsets = (
        (
            "Loan Information",
            {"fields": ("loan_id", "reference_number", "user", "loan_type", "purpose")},
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "amount_requested",
                    "amount_approved",
                    "interest_rate",
                    "disbursement_account",
                )
            },
        ),
        (
            "Status & Review",
            {"fields": ("status", "reviewed_by", "admin_notes", "rejection_reason")},
        ),
        (
            "Timeline",
            {
                "fields": (
                    "application_date",
                    "review_date",
                    "approval_date",
                    "disbursement_date",
                    "days_since_application",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            "pending": "orange",
            "approved": "blue",
            "rejected": "red",
            "disbursed": "green",
            "active": "purple",
            "completed": "gray",
            "cancelled": "black",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "disbursement_account", "reviewed_by")
        )

    actions = [
        "approve_selected_loans",
        "reject_selected_loans",
        "disburse_approved_loans",
    ]

    def approve_selected_loans(self, request, queryset):
        """Approve selected loan applications"""
        updated = 0
        for loan in queryset.filter(status="pending"):
            try:
                with db_transaction.atomic():
                    # Record old status for tracking
                    old_status = loan.status

                    # Approve the loan
                    loan.approve_loan(admin_user=request.user)

                    # Create status update record
                    LoanStatusUpdate.objects.create(
                        loan=loan,
                        old_status=old_status,
                        new_status="approved",
                        updated_by=request.user,
                        notes=f"Loan approved by admin: {request.user.username}",
                    )

                    # Create notification for user
                    Notification.objects.create(
                        user=loan.user,
                        title="Loan Application Approved",
                        message=f"Great news! Your loan application for ${loan.amount_approved} has been approved. Reference: {loan.reference_number}",
                        notification_type="loan",
                        priority="high",
                    )

                    updated += 1
            except Exception as e:
                messages.error(
                    request, f"Error approving loan {loan.reference_number}: {str(e)}"
                )

        self.message_user(
            request, f"{updated} loan applications approved successfully."
        )

    approve_selected_loans.short_description = "Approve selected loan applications"

    def reject_selected_loans(self, request, queryset):
        """Reject selected loan applications"""
        updated = 0
        for loan in queryset.filter(status="pending"):
            try:
                with db_transaction.atomic():
                    # Record old status for tracking
                    old_status = loan.status

                    # Reject the loan
                    loan.reject_loan(
                        admin_user=request.user,
                        reason="Application did not meet approval criteria",
                        notes=f"Loan rejected by admin: {request.user.username}",
                    )

                    # Create status update record
                    LoanStatusUpdate.objects.create(
                        loan=loan,
                        old_status=old_status,
                        new_status="rejected",
                        updated_by=request.user,
                        notes=f"Loan rejected by admin: {request.user.username}",
                    )

                    # Create notification for user
                    Notification.objects.create(
                        user=loan.user,
                        title="Loan Application Update",
                        message=f"Your loan application (Reference: {loan.reference_number}) has been reviewed. Please check your loan dashboard for details.",
                        notification_type="loan",
                        priority="normal",
                    )

                    updated += 1
            except Exception as e:
                messages.error(
                    request, f"Error rejecting loan {loan.reference_number}: {str(e)}"
                )

        self.message_user(request, f"{updated} loan applications rejected.")

    reject_selected_loans.short_description = "Reject selected loan applications"

    def disburse_approved_loans(self, request, queryset):
        """Disburse approved loans (add money to user accounts)"""
        updated = 0
        for loan in queryset.filter(status="approved"):
            try:
                with db_transaction.atomic():
                    # Get the disbursement account
                    if not loan.disbursement_account:
                        # Get user's primary account
                        primary_account = BankAccount.objects.filter(
                            user=loan.user, is_primary=True
                        ).first()
                        if not primary_account:
                            messages.error(
                                request,
                                f"No primary account found for user {loan.user.username}",
                            )
                            continue
                        loan.disbursement_account = primary_account
                        loan.save()

                    # Add money to user's account
                    account = loan.disbursement_account
                    disbursement_amount = loan.amount_approved
                    account.balance += disbursement_amount
                    account.save()

                    # Create transaction record
                    Transaction.objects.create(
                        user=loan.user,
                        from_account=None,  # Bank/System account
                        to_account=account,
                        amount=disbursement_amount,
                        transaction_type="deposit",
                        description=f"Loan disbursement - {loan.reference_number}",
                        reference_number=f"LOAN-{loan.reference_number}",
                        status="completed",
                    )

                    # Record old status for tracking
                    old_status = loan.status

                    # Mark loan as disbursed
                    loan.disburse_loan(admin_user=request.user)

                    # Create status update record
                    LoanStatusUpdate.objects.create(
                        loan=loan,
                        old_status=old_status,
                        new_status="disbursed",
                        updated_by=request.user,
                        notes=f"Loan disbursed by admin: {request.user.username}. Amount: ${disbursement_amount}",
                    )

                    # Create notification for user
                    Notification.objects.create(
                        user=loan.user,
                        title="Loan Disbursed",
                        message=f"Your loan of ${disbursement_amount} has been successfully deposited to your account. Reference: {loan.reference_number}",
                        notification_type="loan",
                        priority="high",
                    )

                    updated += 1
            except Exception as e:
                messages.error(
                    request, f"Error disbursing loan {loan.reference_number}: {str(e)}"
                )

        self.message_user(request, f"{updated} loans disbursed successfully.")

    disburse_approved_loans.short_description = (
        "Disburse approved loans (Add money to accounts)"
    )


@admin.register(LoanStatusUpdate)
class LoanStatusUpdateAdmin(admin.ModelAdmin):
    """Admin interface for Loan Status Updates"""

    list_display = ("loan", "old_status", "new_status", "updated_by", "created_at")
    list_filter = ("old_status", "new_status", "created_at")
    search_fields = (
        "loan__reference_number",
        "loan__user__username",
        "updated_by__username",
    )
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            "Status Change",
            {"fields": ("loan", "old_status", "new_status", "updated_by")},
        ),
        ("Details", {"fields": ("notes", "created_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("loan", "loan__user", "updated_by")
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Customize admin site headers
admin.site.site_header = "BetaBank Loan Administration"
admin.site.site_title = "BetaBank Loan Admin"
admin.site.index_title = "Loan Management Panel"
