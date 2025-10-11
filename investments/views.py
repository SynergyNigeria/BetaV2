from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction as db_transaction
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import json

from .models import Investment, InvestmentPlan, InvestmentTransaction
from banking.models import BankAccount
from transactions.models import Transaction
from accounts.models import UserProfile


@login_required
def investments_dashboard(request):
    """Main investments dashboard showing active investments and available plans"""
    try:
        # Get user's active investments
        active_investments = Investment.objects.filter(
            user=request.user, status="active"
        ).select_related("plan", "from_account")

        # Get available investment plans
        available_plans = InvestmentPlan.objects.filter(is_active=True)

        # Get user's primary bank account
        primary_account = BankAccount.objects.filter(
            user=request.user, is_primary=True
        ).first()

        # Calculate total invested amount and expected returns
        total_invested = sum(inv.principal_amount for inv in active_investments)
        total_expected_returns = sum(inv.expected_returns for inv in active_investments)

        # Get recent investment history
        recent_investments = Investment.objects.filter(
            user=request.user
        ).select_related("plan")[:5]

        context = {
            "active_investments": active_investments,
            "available_plans": available_plans,
            "primary_account": primary_account,
            "total_invested": total_invested,
            "total_expected_returns": total_expected_returns,
            "recent_investments": recent_investments,
            "total_profit": (
                total_expected_returns - total_invested
                if total_expected_returns and total_invested
                else 0
            ),
        }

        return render(request, "investments/dashboard.html", context)

    except Exception as e:
        messages.error(request, f"Error loading investments dashboard: {str(e)}")
        return render(request, "investments/dashboard.html", {"error": str(e)})


@login_required
def investment_plans(request):
    """Display available investment plans"""
    plans = InvestmentPlan.objects.filter(is_active=True)
    primary_account = BankAccount.objects.filter(
        user=request.user, is_primary=True
    ).first()

    context = {
        "plans": plans,
        "primary_account": primary_account,
    }
    return render(request, "investments/plans.html", context)


@login_required
@require_POST
def create_investment(request):
    """Create a new investment"""
    try:
        data = json.loads(request.body)
        plan_id = data.get("plan_id")
        amount = Decimal(str(data.get("amount", 0)))

        if not plan_id or amount <= 0:
            return JsonResponse({"success": False, "error": "Invalid plan or amount"})

        # Get investment plan
        plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)

        # Validate amount
        if amount < plan.minimum_amount:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Minimum investment amount is ${plan.minimum_amount}",
                }
            )

        if plan.maximum_amount and amount > plan.maximum_amount:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Maximum investment amount is ${plan.maximum_amount}",
                }
            )

        # Get user's primary account
        primary_account = get_object_or_404(
            BankAccount, user=request.user, is_primary=True
        )

        # Check balance
        if primary_account.balance < amount:
            return JsonResponse(
                {"success": False, "error": "Insufficient balance for this investment"}
            )

        # Create investment with database transaction
        with db_transaction.atomic():
            # Deduct from account
            primary_account.balance -= amount
            primary_account.save()

            # Create investment
            investment = Investment.objects.create(
                user=request.user,
                plan=plan,
                principal_amount=amount,
                from_account=primary_account,
            )

            # Create bank transaction record
            Transaction.objects.create(
                user=request.user,
                from_account=primary_account,
                to_account=None,
                amount=amount,
                transaction_type="investment",
                description=f"Investment in {plan.name}",
                reference_number=investment.transaction_reference,
                status="completed",
            )

            # Create investment transaction record
            InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type="investment",
                amount=amount,
                description=f"New investment in {plan.name}",
            )

        return JsonResponse(
            {
                "success": True,
                "message": f"Successfully invested ${amount} in {plan.name}",
                "investment_id": str(investment.investment_id),
                "expected_returns": str(investment.expected_returns),
                "maturity_date": investment.maturity_date.strftime("%B %d, %Y"),
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error creating investment: {str(e)}"}
        )


@login_required
def investment_detail(request, investment_id):
    """View details of a specific investment"""
    investment = get_object_or_404(
        Investment, investment_id=investment_id, user=request.user
    )

    # Get investment transactions
    transactions = investment.transactions.all()

    context = {
        "investment": investment,
        "transactions": transactions,
    }

    return render(request, "investments/detail.html", context)


@login_required
@require_POST
def withdraw_investment(request, investment_id):
    """Withdraw a matured investment"""
    try:
        investment = get_object_or_404(
            Investment, investment_id=investment_id, user=request.user, status="active"
        )

        if not investment.is_matured:
            return JsonResponse(
                {"success": False, "error": "Investment has not matured yet"}
            )

        # Get user's primary account
        primary_account = get_object_or_404(
            BankAccount, user=request.user, is_primary=True
        )

        # Process withdrawal
        with db_transaction.atomic():
            # Add returns to account
            returns_amount = investment.expected_returns
            primary_account.balance += returns_amount
            primary_account.save()

            # Update investment status
            investment.status = "withdrawn"
            investment.actual_returns = returns_amount
            investment.withdrawal_date = timezone.now()
            investment.save()

            # Create bank transaction record
            Transaction.objects.create(
                user=request.user,
                from_account=None,
                to_account=primary_account,
                amount=returns_amount,
                transaction_type="investment_withdrawal",
                description=f"Investment withdrawal: {investment.plan.name}",
                reference_number=f"WD-{investment.transaction_reference}",
                status="completed",
            )

            # Create investment transaction record
            InvestmentTransaction.objects.create(
                investment=investment,
                transaction_type="withdrawal",
                amount=returns_amount,
                description=f"Investment withdrawal with returns",
            )

        return JsonResponse(
            {
                "success": True,
                "message": f"Successfully withdrew ${returns_amount}",
                "amount": str(returns_amount),
            }
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Error processing withdrawal: {str(e)}"}
        )


@login_required
def get_plan_details(request, plan_id):
    """Get investment plan details via AJAX"""
    try:
        plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
        primary_account = BankAccount.objects.filter(
            user=request.user, is_primary=True
        ).first()

        return JsonResponse(
            {
                "success": True,
                "plan": {
                    "id": plan.id,
                    "name": plan.name,
                    "description": plan.description,
                    "interest_rate": str(plan.interest_rate),
                    "duration_days": plan.duration_days,
                    "minimum_amount": str(plan.minimum_amount),
                    "maximum_amount": (
                        str(plan.maximum_amount) if plan.maximum_amount else None
                    ),
                    "plan_type": plan.plan_type,
                },
                "user_balance": (
                    str(primary_account.balance) if primary_account else "0.00"
                ),
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def calculate_returns(request):
    """Calculate expected returns for a given amount and plan"""
    try:
        plan_id = request.GET.get("plan_id")
        amount = Decimal(str(request.GET.get("amount", 0)))

        if not plan_id or amount <= 0:
            return JsonResponse({"success": False, "error": "Invalid plan or amount"})

        plan = get_object_or_404(InvestmentPlan, id=plan_id, is_active=True)
        expected_returns = plan.calculate_returns(amount)
        profit = expected_returns - amount

        return JsonResponse(
            {
                "success": True,
                "principal": str(amount),
                "expected_returns": str(expected_returns),
                "profit": str(profit),
                "interest_rate": str(plan.interest_rate),
                "duration_days": plan.duration_days,
            }
        )

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# Legacy view functions (keeping for compatibility)
def investments_view(request):
    return redirect("investments:dashboard")


def create_investment_view(request):
    return redirect("investments:plans")


def dynamic_investment_view(request):
    return redirect("investments:dashboard")


def invest_dynamic_view(request):
    return redirect("investments:plans")


def performance_view(request):
    return redirect("investments:dashboard")


def withdraw_investment_view(request, investment_id):
    return redirect("investments:detail", investment_id=investment_id)
