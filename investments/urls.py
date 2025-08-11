from django.urls import path
from . import views

app_name = "investments"

urlpatterns = [
    # Investment Portfolio URLs
    path("", views.investments_view, name="investments"),
    path("create/", views.create_investment_view, name="create"),
    path("<int:investment_id>/", views.investment_detail_view, name="detail"),
    # Dynamic Investment URLs
    path("dynamic/", views.dynamic_investment_view, name="dynamic"),
    path("dynamic/invest/", views.invest_dynamic_view, name="invest_dynamic"),
    # Performance URLs
    path("performance/", views.performance_view, name="performance"),
    path(
        "withdraw/<int:investment_id>/", views.withdraw_investment_view, name="withdraw"
    ),
]
