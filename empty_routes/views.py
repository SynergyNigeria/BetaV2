from django.shortcuts import render

# Create your views here.
def investment_services(request):
    return render(request, 'investment-services.html')

def business_banking(request):
    return render(request, 'business-banking.html')

def personal_banking(request):
    return render(request, 'personal-banking.html')

def credit_cards(request):
    return render(request, 'credit-cards.html')

def customer_service(request):
    return render(request, 'customer-service.html')

def loans_mortgages(request):
    return render(request, 'loans-mortgages.html')

def online_banking_help(request):
    return render(request, 'online-banking-help.html')

def privacy_policy(request):
    return render(request, 'privacy-policy.html')

def security_center(request):
    return render(request, 'security-center.html')

def terms_of_service(request):
    return render(request, 'terms-of-service.html')