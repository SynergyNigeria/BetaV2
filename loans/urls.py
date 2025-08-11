from django.urls import path
from . import views

app_name = "loans"

urlpatterns = [
    # Loan Management URLs
    path("", views.loans_view, name="loans"),
    path("apply/", views.apply_loan_view, name="apply"),
    path("<int:loan_id>/", views.loan_detail_view, name="detail"),
    # Payment URLs
    path("<int:loan_id>/payment/", views.make_payment_view, name="make_payment"),
    path(
        "<int:loan_id>/schedule/", views.payment_schedule_view, name="payment_schedule"
    ),
    # Loan Calculator
    path("calculator/", views.loan_calculator_view, name="calculator"),
]
