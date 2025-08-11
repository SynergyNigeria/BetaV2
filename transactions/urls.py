from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    # Transfer URLs
    path("transfer/", views.transfer_view, name="transfer"),
    path("transfer/initiate/", views.initiate_transfer, name="initiate_transfer"),
    path("transfer/verify-occid/", views.verify_occid, name="verify_occid"),
    path(
        "transfer/recipient-info/", views.get_recipient_info, name="get_recipient_info"
    ),
    # Deposit URLs
    path("deposit/", views.deposit_view, name="deposit"),
    path("deposit/usdt/", views.usdt_deposit_view, name="usdt_deposit"),
    path("deposit/giftcard/", views.giftcard_deposit_view, name="giftcard_deposit"),
    # AJAX deposit submission endpoints
    path("deposit/usdt/submit/", views.submit_usdt_deposit, name="submit_usdt_deposit"),
    path(
        "deposit/giftcard/submit/",
        views.submit_giftcard_deposit,
        name="submit_giftcard_deposit",
    ),
    path(
        "deposit/verify/<str:reference>/",
        views.verify_deposit_view,
        name="verify_deposit",
    ),
    # Transaction History
    path("history/", views.transaction_history_view, name="history"),
    path("history/<int:transaction_id>/", views.transaction_detail_view, name="detail"),
    # Transaction Actions
    path("cancel/<int:transaction_id>/", views.cancel_transaction_view, name="cancel"),
    path(
        "receipt/<str:transaction_id>/", views.download_receipt, name="download_receipt"
    ),
]
