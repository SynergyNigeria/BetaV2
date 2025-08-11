from django.shortcuts import render
from django.http import HttpResponse

# Investment Portfolio Views


def investments_view(request):
    return render(request, "investments/investments.html")


def create_investment_view(request):
    return render(request, "investments/create.html")


def investment_detail_view(request, investment_id):
    return render(request, "investments/detail.html", {"investment_id": investment_id})


# Dynamic Investment Views


def dynamic_investment_view(request):
    return render(request, "investments/dynamic.html")


def invest_dynamic_view(request):
    return render(request, "investments/invest_dynamic.html")


# Performance Views


def performance_view(request):
    return render(request, "investments/performance.html")


def withdraw_investment_view(request, investment_id):
    return render(
        request, "investments/withdraw.html", {"investment_id": investment_id}
    )
