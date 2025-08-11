from django.urls import path
from . import views

app_name = "route"

urlpatterns = [
    path('investment-services/', views.investment_services, name='investment_services'),
    path('business-banking/', views.business_banking, name='business_banking'),
    path('personal-banking/', views.personal_banking, name='personal_banking'),
    path('credit-cards/', views.credit_cards, name='credit_cards'),
    path('loans-mortgages/', views.loans_mortgages, name='loans_mortgages'),
    path('online-banking-help/', views.online_banking_help, name='online_banking_help'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('security-center/', views.security_center, name='security_center'),
    path('customer-service/', views.customer_service, name='customer_service'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
]