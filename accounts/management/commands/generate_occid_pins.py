from django.core.management.base import BaseCommand
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Generate OCCID PINs for all users who do not have one"

    def handle(self, *args, **options):
        profiles_without_occid = UserProfile.objects.filter(
            occid_pin__isnull=True
        ) | UserProfile.objects.filter(occid_pin="")
        count = profiles_without_occid.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("All users already have OCCID PINs"))
            return

        self.stdout.write(f"Found {count} users without OCCID PINs. Generating...")

        updated_count = 0
        for profile in profiles_without_occid:
            profile.save()  # This will trigger the OCCID PIN generation
            updated_count += 1
            self.stdout.write(f"Generated OCCID PIN for user: {profile.user.username}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated OCCID PINs for {updated_count} users"
            )
        )
