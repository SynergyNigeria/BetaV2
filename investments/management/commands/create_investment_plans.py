from django.core.management.base import BaseCommand
from decimal import Decimal
from investments.models import InvestmentPlan


class Command(BaseCommand):
    help = "Create sample investment plans for testing"

    def handle(self, *args, **options):
        # Clear existing plans first
        InvestmentPlan.objects.all().delete()

        # Create sample investment plans
        plans_data = [
            {
                "name": "Basic Savings Plan",
                "plan_type": "basic",
                "description": "Perfect for beginners looking to start their investment journey with low risk and steady returns.",
                "minimum_amount": Decimal("100.00"),
                "maximum_amount": Decimal("5000.00"),
                "interest_rate": Decimal("8.50"),
                "duration_days": 14,
                "is_active": True,
            },
            {
                "name": "Premium Growth Plan",
                "plan_type": "premium",
                "description": "Ideal for experienced investors seeking moderate risk with higher returns over a short period.",
                "minimum_amount": Decimal("500.00"),
                "maximum_amount": Decimal("15000.00"),
                "interest_rate": Decimal("12.75"),
                "duration_days": 14,
                "is_active": True,
            },
            {
                "name": "Gold Investment Plan",
                "plan_type": "gold",
                "description": "High-yield investment plan for serious investors looking for maximum returns with moderate risk.",
                "minimum_amount": Decimal("1000.00"),
                "maximum_amount": Decimal("50000.00"),
                "interest_rate": Decimal("18.50"),
                "duration_days": 14,
                "is_active": True,
            },
            {
                "name": "Platinum Elite Plan",
                "plan_type": "platinum",
                "description": "Exclusive premium plan with the highest returns for VIP investors and large capital investments.",
                "minimum_amount": Decimal("5000.00"),
                "maximum_amount": Decimal("100000.00"),
                "interest_rate": Decimal("25.00"),
                "duration_days": 14,
                "is_active": True,
            },
            {
                "name": "Quick Start Plan",
                "plan_type": "basic",
                "description": "Get started immediately with our lowest entry barrier plan designed for new investors.",
                "minimum_amount": Decimal("50.00"),
                "maximum_amount": Decimal("2000.00"),
                "interest_rate": Decimal("6.25"),
                "duration_days": 14,
                "is_active": True,
            },
            {
                "name": "Business Builder Plan",
                "plan_type": "premium",
                "description": "Perfect for small businesses and entrepreneurs looking to grow their capital efficiently.",
                "minimum_amount": Decimal("2500.00"),
                "maximum_amount": Decimal("25000.00"),
                "interest_rate": Decimal("15.75"),
                "duration_days": 14,
                "is_active": True,
            },
        ]

        created_count = 0
        for plan_data in plans_data:
            plan, created = InvestmentPlan.objects.get_or_create(
                name=plan_data["name"], defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created plan: {plan.name} - {plan.interest_rate}%"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Plan already exists: {plan.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully created {created_count} investment plans!"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Total active plans: {InvestmentPlan.objects.filter(is_active=True).count()}"
            )
        )
