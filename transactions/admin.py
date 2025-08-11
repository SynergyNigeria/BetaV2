from .models import Deposit
from django.contrib import admin
from .models import Transaction, TransferSession


# Deposit admin
@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "user",
        "method",
        "amount",
        "status",
        "verified",
        "created_at",
        "card_type",
        "tx_hash",
    )
    list_filter = ("method", "status", "verified", "created_at", "card_type")
    search_fields = (
        "reference_number",
        "user__username",
        "user__email",
        "card_type",
        "tx_hash",
        "card_code",
    )
    readonly_fields = ("reference_number", "created_at", "updated_at", "card_proof")
    fieldsets = (
        (
            "Deposit Info",
            {
                "fields": (
                    "reference_number",
                    "user",
                    "method",
                    "amount",
                    "status",
                    "description",
                )
            },
        ),
        (
            "Gift Card Details",
            {
                "fields": ("card_type", "card_code", "card_proof"),
                "classes": ("collapse",),
            },
        ),
        (
            "USDT Details",
            {"fields": ("tx_hash", "usdt_address"), "classes": ("collapse",)},
        ),
        ("Verification", {"fields": ("verified", "verified_at", "verified_by")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction admin interface"""

    list_display = (
        "transaction_id",
        "user",
        "transaction_type",
        "amount",
        "fee",
        "status",
        "occid_verified",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "status",
        "transfer_type",
        "occid_verified",
        "created_at",
    )

    search_fields = (
        "transaction_id",
        "reference_number",
        "user__username",
        "user__email",
        "recipient_name",
        "recipient_account_holder",
    )

    readonly_fields = (
        "transaction_id",
        "reference_number",
        "created_at",
        "updated_at",
        "occid_verified_at",
        "completed_at",
    )

    fieldsets = (
        (
            "Transaction Information",
            {
                "fields": (
                    "transaction_id",
                    "reference_number",
                    "transaction_type",
                    "status",
                )
            },
        ),
        ("Financial Details", {"fields": ("amount", "fee", "description")}),
        ("Account Information", {"fields": ("user", "from_account", "to_account")}),
        (
            "Recipient Information",
            {
                "fields": (
                    "recipient_user",
                    "recipient_name",
                    "recipient_account_number",
                    "recipient_account_holder",
                    "recipient_bank_name",
                    "routing_swift_code",
                )
            },
        ),
        ("Transfer Details", {"fields": ("transfer_type", "transfer_purpose")}),
        ("Security", {"fields": ("occid_verified", "occid_verified_at")}),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at", "completed_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(TransferSession)
class TransferSessionAdmin(admin.ModelAdmin):
    """Transfer Session admin interface"""

    list_display = (
        "session_id",
        "user",
        "transfer_type",
        "amount",
        "is_active",
        "expires_at",
        "created_at",
    )

    list_filter = ("transfer_type", "bank_transfer_type", "is_active", "created_at")

    search_fields = (
        "session_id",
        "user__username",
        "recipient_identifier",
        "recipient_account_holder",
    )

    readonly_fields = ("session_id", "created_at", "expires_at")

    fieldsets = (
        (
            "Session Information",
            {"fields": ("session_id", "user", "transfer_type", "is_active")},
        ),
        ("Transfer Details", {"fields": ("from_account_id", "amount", "description")}),
        (
            "BetaBank Transfer",
            {"fields": ("recipient_identifier",), "classes": ("collapse",)},
        ),
        (
            "External Bank Transfer",
            {
                "fields": (
                    "bank_transfer_type",
                    "recipient_bank_name",
                    "recipient_account_number",
                    "recipient_account_holder",
                    "routing_swift_code",
                    "transfer_purpose",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Session Management",
            {"fields": ("created_at", "expires_at"), "classes": ("collapse",)},
        ),
    )
