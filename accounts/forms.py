from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "123 Main St, Apt 4B",
                "rows": 2,
            }
        ),
        label="Address",
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "City",
            }
        ),
        label="City",
    )
    state = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "State",
            }
        ),
        label="State",
    )
    zip_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "ZIP Code",
            }
        ),
        label="ZIP Code",
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "John",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Doe",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "you@example.com",
            }
        ),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "(555) 123-4567",
            }
        ),
    )
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500",
            }
        ),
    )
    country = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Country",
            }
        ),
    )
    security_question = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Your first pet's name?",
            }
        ),
    )
    security_answer = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Fluffy",
            }
        ),
    )
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out"
            }
        ),
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Username",
            }
        ),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Password",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full border border-gray-300 rounded-lg px-4 py-3 pl-10 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Confirm Password",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password1",
            "password2",
            "phone_number",
            "date_of_birth",
            "country",
            "address",
            "city",
            "state",
            "zip_code",
            "security_question",
            "security_answer",
            "agree_terms",
        )

    def save(self, commit=True):
        from banking.models import BankAccount, Card
        from datetime import datetime

        # Save User first
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            # Create linked UserProfile with address fields
            profile = UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data["phone_number"],
                date_of_birth=self.cleaned_data["date_of_birth"],
                country=self.cleaned_data["country"],
                address=self.cleaned_data.get("address", ""),
                city=self.cleaned_data.get("city", ""),
                state=self.cleaned_data.get("state", ""),
                zip_code=self.cleaned_data.get("zip_code", ""),
                security_question=self.cleaned_data["security_question"],
                security_answer=self.cleaned_data["security_answer"],
            )
            profile.save()
            # Create a primary BankAccount for the user
            bank_account = BankAccount.objects.create(
                user=user,
                account_type="checking",
                is_primary=True,
            )
            # Create a primary Card for the user, linked to the bank account
            now = datetime.now()
            Card.objects.create(
                user=user,
                bank_account=bank_account,
                card_type="debit",
                is_primary=True,
                expiry_month=now.month,
                expiry_year=now.year + 4,
            )
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "pl-10 py-3 px-4 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-200",
                "placeholder": "Username",
                "autocomplete": "username",
            }
        ),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "id": "password",
                "class": "pl-10 py-3 px-4 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition duration-200",
                "placeholder": "Password",
                "autocomplete": "current-password",
            }
        )
    )
