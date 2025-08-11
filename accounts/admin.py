from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile
from banking.models import BankAccount, Card
from notifications.models import Notification


# Unregister the default User admin
admin.site.unregister(User)


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        ("phone_number", "date_of_birth"),
        ("country", "account_number"),
        ("security_question", "security_answer"),
        ("is_verified", "verification_date"),
        ("occid_pin",),
    )
    readonly_fields = ("account_number", "occid_pin")


class BankAccountInline(admin.TabularInline):
    """Inline admin for BankAccount"""

    model = BankAccount
    extra = 0
    readonly_fields = ("account_number", "created_at")
    fields = (
        "account_type",
        "account_number",
        "balance",
        "is_active",
        "is_primary",
        "created_at",
    )


class CardInline(admin.TabularInline):
    """Inline admin for Cards"""

    model = Card
    extra = 0
    readonly_fields = ("card_number", "cvv", "created_at")
    fields = (
        "card_type",
        "card_number",
        "card_holder_name",
        "status",
        "is_primary",
        "created_at",
    )


class NotificationInline(admin.TabularInline):
    """Inline admin for Notifications"""

    model = Notification
    extra = 0
    readonly_fields = ("created_at",)
    fields = ("title", "notification_type", "priority", "is_read", "created_at")
    ordering = ("-created_at",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Extended User admin with related models"""

    inlines = (UserProfileInline, BankAccountInline, CardInline, NotificationInline)
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
        "get_account_number",
        "get_total_balance",
    )
    list_filter = ("is_staff", "is_active", "date_joined", "profile__is_verified")
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "profile__account_number",
        "profile__phone_number",
    )

    def get_account_number(self, obj):
        """Get user's account number"""
        try:
            return obj.profile.account_number
        except:
            return "No Profile"

    get_account_number.short_description = "Account Number"

    def get_total_balance(self, obj):
        """Get user's total balance across all accounts"""
        total = sum(account.balance for account in obj.bank_accounts.all())
        return f"${total:,.2f}"

    get_total_balance.short_description = "Total Balance"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """UserProfile admin interface"""

    list_display = (
        "user",
        "account_number",
        "phone_number",
        "occid_pin",
        "is_verified",
        "verification_date",
        "created_at",
    )
    list_filter = ("is_verified", "verification_date", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "account_number",
        "phone_number",
        "country",
    )
    readonly_fields = ("account_number", "created_at", "updated_at", "occid_pin")

    fieldsets = (
        ("User Information", {"fields": ("user", "account_number")}),
        (
            "Personal Details",
            {"fields": ("phone_number", "date_of_birth", "country")},
        ),
        ("Security", {"fields": ("security_question", "security_answer", "occid_pin")}),
        ("Verification", {"fields": ("is_verified", "verification_date")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


# Customize admin site headers
admin.site.site_header = "BetaBank Administration"
admin.site.site_title = "BetaBank Admin"
admin.site.index_title = "Welcome to BetaBank Administration Panel"
