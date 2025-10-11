from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import transaction as db_transaction
from decimal import Decimal
import json

from .models import Loan, LoanStatusUpdate
from banking.models import BankAccount
from notifications.models import Notification


@login_required
def loans_dashboard(request):
    """Main loans dashboard showing user's loan applications"""
    try:
        # Get user's loans
        user_loans = Loan.objects.filter(user=request.user).order_by(
            "-application_date"
        )

        # Get user's primary account
        primary_account = BankAccount.objects.filter(
            user=request.user, is_primary=True
        ).first()

        # Calculate loan statistics
        pending_loans = user_loans.filter(status="pending").count()
        approved_loans = user_loans.filter(
            status__in=["approved", "disbursed", "active"]
        ).count()
        total_requested = sum(loan.amount_requested for loan in user_loans)
        total_approved = sum(
            loan.amount_approved or 0
            for loan in user_loans.filter(
                status__in=["approved", "disbursed", "active"]
            )
        )

        context = {
            "user_loans": user_loans,
            "primary_account": primary_account,
            "pending_loans": pending_loans,
            "approved_loans": approved_loans,
            "total_requested": total_requested,
            "total_approved": total_approved,
        }

        return render(request, "loans/dashboard.html", context)

    except Exception as e:
        messages.error(request, f"Error loading loans dashboard: {str(e)}")
        return render(request, "loans/dashboard.html", {"error": str(e)})


@login_required
@require_POST
def apply_for_loan(request):
    """Handle loan application submission"""
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get("amount", 0)))
        loan_type = data.get("loan_type", "quick")
        purpose = data.get("purpose", "")

        if not amount or amount <= 0:
            return JsonResponse(
                {"success": False, "error": "Please enter a valid loan amount"}
            )

        # Basic validation
        if amount < Decimal("100.00"):
            return JsonResponse(
                {"success": False, "error": "Minimum loan amount is $100.00"}
            )

        if amount > Decimal("1000000.00"):
            return JsonResponse(
                {"success": False, "error": "Maximum loan amount is $1,000,000.00"}
            )

        # Get user's primary account for future disbursement
        primary_account = get_object_or_404(
            BankAccount, user=request.user, is_primary=True
        )

        # Create loan application
        loan = Loan.objects.create(
            user=request.user,
            loan_type=loan_type,
            amount_requested=amount,
            purpose=purpose,
            disbursement_account=primary_account,
        )

        # Create notification for user
        Notification.objects.create(
            user=request.user,
            title="Loan Application Submitted",
            message=f"Your loan application for ${amount} has been submitted and is under review. Reference: {loan.reference_number}",
            notification_type="loan",
            priority="normal",
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"Your loan application for ${amount} has been submitted successfully! Reference: {loan.reference_number}. You will be notified when the status changes.",
                "reference_number": loan.reference_number,
                "loan_id": str(loan.loan_id),
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error processing loan application: {str(e)}"}
        )


@login_required
def loan_detail(request, loan_id):
    """View details of a specific loan"""
    loan = get_object_or_404(Loan, loan_id=loan_id, user=request.user)

    # Get status updates
    status_updates = loan.status_updates.all()

    context = {
        "loan": loan,
        "status_updates": status_updates,
    }

    return render(request, "loans/detail.html", context)


@login_required
def get_loan_status(request, loan_id):
    """Get loan status via AJAX"""
    try:
        loan = get_object_or_404(Loan, loan_id=loan_id, user=request.user)

        return JsonResponse(
            {
                "success": True,
                "loan": {
                    "reference_number": loan.reference_number,
                    "status": loan.status,
                    "amount_requested": str(loan.amount_requested),
                    "amount_approved": (
                        str(loan.amount_approved) if loan.amount_approved else None
                    ),
                    "application_date": loan.application_date.strftime("%B %d, %Y"),
                    "days_since_application": loan.days_since_application,
                },
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# Legacy view functions (keeping for compatibility)
def loans_view(request):
    return redirect("loans:dashboard")


def apply_loan_view(request):
    return redirect("loans:dashboard")


def loan_detail_view(request, loan_id):
    return redirect("loans:detail", loan_id=loan_id)


def make_payment_view(request, loan_id):
    return redirect("loans:detail", loan_id=loan_id)


def payment_schedule_view(request, loan_id):
    return redirect("loans:detail", loan_id=loan_id)


def loan_calculator_view(request):
    return redirect("loans:dashboard")
