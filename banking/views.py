from django.shortcuts import render
from django.http import HttpResponse

# Banking Account Views


def accounts_view(request):
    return render(request, "banking/accounts.html")


def create_account_view(request):
    return render(request, "banking/create_account.html")


def account_detail_view(request, account_id):
    return render(request, "banking/account_detail.html", {"account_id": account_id})


# Cards Views


def cards_view(request):
    return render(request, "banking/cards.html")


def apply_card_view(request):
    return render(request, "banking/apply_card.html")


def card_detail_view(request, card_id):
    return render(request, "banking/card_detail.html", {"card_id": card_id})


# Transfer Views


def transfer_view(request):
    return render(request, "banking/transfer.html")


def transfer_history_view(request):
    return render(request, "banking/transfer_history.html")
