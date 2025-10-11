from django.urls import path
from . import views

app_name = "investments"

urlpatterns = [
    # Main Investment URLs
    path("", views.investments_dashboard, name="dashboard"),
    path("plans/", views.investment_plans, name="plans"),
    path("detail/<uuid:investment_id>/", views.investment_detail, name="detail"),
    # AJAX URLs
    path("create/", views.create_investment, name="create"),
    path("withdraw/<uuid:investment_id>/", views.withdraw_investment, name="withdraw"),
    path("plan/<int:plan_id>/", views.get_plan_details, name="plan_details"),
    path("calculate/", views.calculate_returns, name="calculate_returns"),
    # Legacy URLs (redirects)
    path("investments/", views.investments_view, name="investments"),
    path("create_investment/", views.create_investment_view, name="create_investment"),
    path("dynamic/", views.dynamic_investment_view, name="dynamic"),
    path("dynamic/invest/", views.invest_dynamic_view, name="invest_dynamic"),
    path("performance/", views.performance_view, name="performance"),
    path(
        "withdraw_old/<int:investment_id>/",
        views.withdraw_investment_view,
        name="withdraw_old",
    ),
]
