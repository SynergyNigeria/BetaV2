from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .forms import UserRegistrationForm, UserLoginForm
from django.http import HttpResponse
from banking.models import BankAccount, Card
from notifications.models import Notification
from django.contrib.auth.decorators import login_required

# Register view


def register_view(request):
    from django.db import IntegrityError

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        # Extract fields for duplicate checks
        email = request.POST.get("email", "").strip().lower()
        username = request.POST.get("username", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        duplicate = False

        # Check for existing email
        if User.objects.filter(email__iexact=email).exists():
            form.add_error("email", "A user with this email already exists.")
            duplicate = True

        # Check for existing username
        if User.objects.filter(username__iexact=username).exists():
            form.add_error("username", "This username is already taken.")
            duplicate = True

        # Check for existing phone number in UserProfile
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            form.add_error(
                "phone_number", "A user with this phone number already exists."
            )
            duplicate = True

        if form.is_valid() and not duplicate:
            try:
                user = form.save()
                messages.success(request, "Registration successful. Please log in.")
                return redirect("accounts:login")
            except Exception as e:
                messages.error(
                    request,
                    f"An error occurred during registration: {str(e)}",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserRegistrationForm()

    return render(request, "register.html", {"form": form})


# Login view


def login_view(request):
    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, "Login successful!")
                return redirect("accounts:dashboard")
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = UserLoginForm()
    return render(request, "login.html", {"form": form})


# Logout view


def logout_view(request):
    auth_logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


# Dashboard view


def dashboard_view(request):
    user = request.user
    # Get all active bank accounts for the user
    bank_accounts = BankAccount.objects.filter(user=user, is_active=True)
    total_balance = sum(account.balance for account in bank_accounts)
    total_accounts = bank_accounts.count()
    cards = Card.objects.filter(user=user)
    total_cards = cards.count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    recent_notifications = Notification.objects.filter(user=user).order_by(
        "-created_at"
    )[:5]
    user_profile = getattr(user, "profile", None)
    context = {
        "user": user,
        "user_profile": user_profile,
        "bank_accounts": bank_accounts,
        "cards": cards,
        "total_balance": total_balance,
        "total_accounts": total_accounts,
        "total_cards": total_cards,
        "unread_notifications": unread_notifications,
        "recent_notifications": recent_notifications,
    }
    return render(request, "dashboard.html", context)


# Settings view


def settings_view(request):
    return render(request, "settings.html")


# Support view


def support_view(request):
    return render(request, "support.html")


# Profile view


def profile_view(request):
    return render(request, "accounts/profile.html")


def profile_update_view(request):
    return render(request, "accounts/profile_update.html")


# Notifications views
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    context = {
        "notifications": notifications,
    }
    return render(request, "notifications.html", context)


@login_required
def mark_notification_read(request, notification_id):
    if request.method == "POST":
        notification = Notification.objects.filter(
            id=notification_id, user=request.user
        ).first()
        if notification and not notification.is_read:
            notification.is_read = True
            notification.save()
    return redirect("accounts:notifications")


@login_required
def mark_all_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
    return redirect("accounts:notifications")
