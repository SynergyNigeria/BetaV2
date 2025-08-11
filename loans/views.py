from django.shortcuts import render
from django.http import HttpResponse

# Loan Management Views


def loans_view(request):
    return render(request, "loans/loans.html")


def apply_loan_view(request):
    return render(request, "loans/apply.html")


def loan_detail_view(request, loan_id):
    return render(request, "loans/detail.html", {"loan_id": loan_id})


# Payment Views


def make_payment_view(request, loan_id):
    return render(request, "loans/make_payment.html", {"loan_id": loan_id})


def payment_schedule_view(request, loan_id):
    return render(request, "loans/payment_schedule.html", {"loan_id": loan_id})


# Loan Calculator


def loan_calculator_view(request):
    return render(request, "loans/calculator.html")
