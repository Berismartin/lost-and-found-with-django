import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from items.models import Item


User = get_user_model()


class Command(BaseCommand):
    help = "Populate a rich dataset of items to power dashboard visualizations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--total",
            type=int,
            default=60,
            help="Total number of synthetic items to create (default: 60).",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove previously seeded demo items before creating new ones.",
        )
        parser.add_argument(
            "--username",
            default="sekatawa.eric",
            help="Username that will own the seeded items (default: sekatawa.eric).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        total_items = options["total"]
        username = options["username"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": username.split(".")[0].title(),
                "last_name": username.split(".")[-1].title(),
                "email": f"{username.replace('.', '+')}@example.com",
            },
        )
        if created:
            user.set_password("changeme123")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}' with temporary password 'changeme123'."))
        else:
            self.stdout.write(self.style.HTTP_INFO(f"Using existing user '{username}'"))

        if options["flush"]:
            deleted, _ = Item.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} existing items for '{username}'."))

        categories = [choice[0] for choice in Item.CATEGORY_CHOICES]
        statuses = [choice[0] for choice in Item.STATUS_CHOICES]
        status_weights = {
            "lost": 0.40,
            "found": 0.25,
            "returned_to_owner": 0.20,
            "archived": 0.15,
        }
        locations = [
            "Main Library - Quiet Reading Room",
            "Innovation Hub - Conference Room B",
            "Campus Gym - Locker Room",
            "Downtown Coffee Shop - Oak & 5th",
            "Riverside Park Dog Run",
            "Residence Hall Laundry Room",
            "Computer Science Building - Room 204",
            "International Student Office Lobby",
            "Makerspace Garage",
            "City Arts Center Auditorium",
        ]
        contact_templates = [
            "Call {name} at +1-555-{suffix}",
            "Email {name}@example.com",
            "Drop at reception desk before 6 PM",
            "Reply via lost & found inbox",
        ]
        base_now = timezone.now()

        created_count = 0
        for index in range(total_items):
            category = random.choice(categories)
            status = random.choices(
                population=list(status_weights.keys()),
                weights=list(status_weights.values()),
                k=1,
            )[0]
            item_location = random.choice(locations)
            days_ago = random.randint(0, 150)
            created_at = base_now - timedelta(days=days_ago, hours=random.randint(0, 23))
            description = (
                f"{category.title()} item reported {status.replace('_', ' ')}. "
                f"Auto-generated for dashboard demos."
            )
            title = f"{category.title()} sample #{index + 1}"
            contact_info = random.choice(contact_templates).format(
                name=username.split(".")[0],
                suffix=f"{random.randint(1000, 9999)}",
            )

            item = Item.objects.create(
                title=title,
                description=description,
                category=category,
                status=status,
                user=user,
                location_lost_found=item_location,
                date_lost_found=created_at,
                contact_info=contact_info,
                is_active=status in {"lost", "found"},
            )

            resolution_delay_days = random.randint(0, 30)
            if status in {"found", "returned_to_owner"}:
                updated_at = created_at + timedelta(days=resolution_delay_days)
            elif status == "archived":
                updated_at = created_at + timedelta(days=random.randint(7, 90))
            else:
                updated_at = created_at

            Item.objects.filter(pk=item.pk).update(
                created_at=created_at,
                updated_at=updated_at,
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created_count} items for dashboard analytics."))
        self.stdout.write(self.style.HTTP_INFO("Run the dashboard to verify charts now show richer data."))

