from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import InvestmentPlan, Investment, InvestmentTransaction


@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    """Admin interface for Investment Plans"""

    list_display = (
        "name",
        "plan_type",
        "interest_rate",
        "duration_days",
        "minimum_amount",
        "maximum_amount",
        "is_active",
        "created_at",
    )
    list_filter = ("plan_type", "is_active", "created_at")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Plan Information", {"fields": ("name", "plan_type", "description")}),
        (
            "Investment Terms",
            {
                "fields": (
                    "interest_rate",
                    "duration_days",
                    "minimum_amount",
                    "maximum_amount",
                )
            },
        ),
        ("Status", {"fields": ("is_active",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


class InvestmentTransactionInline(admin.TabularInline):
    """Inline admin for Investment Transactions"""

    model = InvestmentTransaction
    extra = 0
    readonly_fields = ("reference", "created_at")
    fields = ("transaction_type", "amount", "description", "reference", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """Admin interface for User Investments"""

    list_display = (
        "user",
        "plan",
        "principal_amount",
        "expected_returns",
        "status",
        "progress_display",
        "start_date",
        "maturity_date",
    )
    list_filter = ("status", "plan", "start_date", "maturity_date")
    search_fields = (
        "user__username",
        "user__email",
        "transaction_reference",
        "investment_id",
    )
    readonly_fields = (
        "investment_id",
        "transaction_reference",
        "expected_returns",
        "maturity_date",
        "progress_percentage",
        "is_matured",
        "days_remaining",
        "created_at",
        "updated_at",
    )
    inlines = [InvestmentTransactionInline]

    fieldsets = (
        (
            "Investment Information",
            {"fields": ("investment_id", "user", "plan", "transaction_reference")},
        ),
        (
            "Financial Details",
            {
                "fields": (
                    "principal_amount",
                    "expected_returns",
                    "actual_returns",
                    "from_account",
                )
            },
        ),
        (
            "Investment Timeline",
            {
                "fields": (
                    "start_date",
                    "maturity_date",
                    "withdrawal_date",
                    "progress_percentage",
                    "days_remaining",
                    "is_matured",
                )
            },
        ),
        ("Status", {"fields": ("status",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def progress_display(self, obj):
        """Display investment progress as a visual bar"""
        progress = obj.progress_percentage
        if progress >= 100:
            color = "green"
            status = "Completed"
        elif progress >= 75:
            color = "blue"
            status = f"{progress:.0f}%"
        elif progress >= 50:
            color = "orange"
            status = f"{progress:.0f}%"
        else:
            color = "red"
            status = f"{progress:.0f}%"

        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; color: white; font-size: 11px; line-height: 20px;">{}</div>'
            "</div>",
            min(progress, 100),
            color,
            status,
        )

    progress_display.short_description = "Progress"

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("user", "plan", "from_account")
        )

    actions = ["mark_as_matured", "mark_as_withdrawn"]

    def mark_as_matured(self, request, queryset):
        """Mark selected investments as matured"""
        updated = queryset.filter(status="active").update(status="matured")
        self.message_user(request, f"{updated} investments marked as matured.")

    mark_as_matured.short_description = "Mark selected investments as matured"

    def mark_as_withdrawn(self, request, queryset):
        """Mark selected investments as withdrawn"""
        from django.utils import timezone

        updated = 0
        for investment in queryset.filter(status__in=["active", "matured"]):
            investment.status = "withdrawn"
            investment.withdrawal_date = timezone.now()
            investment.actual_returns = investment.expected_returns
            investment.save()
            updated += 1
        self.message_user(request, f"{updated} investments marked as withdrawn.")

    mark_as_withdrawn.short_description = "Mark selected investments as withdrawn"


@admin.register(InvestmentTransaction)
class InvestmentTransactionAdmin(admin.ModelAdmin):
    """Admin interface for Investment Transactions"""

    list_display = (
        "investment",
        "transaction_type",
        "amount",
        "reference",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("investment__user__username", "reference", "description")
    readonly_fields = ("reference", "created_at")

    fieldsets = (
        (
            "Transaction Information",
            {"fields": ("investment", "transaction_type", "reference")},
        ),
        ("Details", {"fields": ("amount", "description")}),
        ("Timestamp", {"fields": ("created_at",)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("investment", "investment__user")
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Customize admin site headers
admin.site.site_header = "BetaBank Investment Administration"
admin.site.site_title = "BetaBank Investment Admin"
admin.site.index_title = "Investment Management Panel"
