from django.urls import path
from . import views

app_name = "banking"

urlpatterns = [
    # Banking Account URLs
    path("accounts/", views.accounts_view, name="accounts"),
    path("accounts/create/", views.create_account_view, name="create_account"),
    path(
        "accounts/<int:account_id>/", views.account_detail_view, name="account_detail"
    ),
    # Cards URLs
    path("cards/", views.cards_view, name="cards"),
    path("cards/apply/", views.apply_card_view, name="apply_card"),
    path("cards/<int:card_id>/", views.card_detail_view, name="card_detail"),
    # Transfer URLs
    path("transfer/", views.transfer_view, name="transfer"),
    path("transfer/history/", views.transfer_history_view, name="transfer_history"),
]
