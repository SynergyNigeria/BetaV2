from django.urls import path
from . import views

app_name = "loans"

urlpatterns = [
    # Main Loan URLs
    path("", views.loans_dashboard, name="dashboard"),
    path("detail/<uuid:loan_id>/", views.loan_detail, name="detail"),
    # AJAX URLs
    path("apply/", views.apply_for_loan, name="apply"),
    path("status/<uuid:loan_id>/", views.get_loan_status, name="status"),
    # Legacy URLs (redirects)
    path("loans/", views.loans_view, name="loans"),
    path("apply_loan/", views.apply_loan_view, name="apply_loan"),
    path("old/<int:loan_id>/", views.loan_detail_view, name="detail_old"),
    path("old/<int:loan_id>/payment/", views.make_payment_view, name="make_payment"),
    path(
        "old/<int:loan_id>/schedule/",
        views.payment_schedule_view,
        name="payment_schedule",
    ),
    path("calculator/", views.loan_calculator_view, name="calculator"),
]
