from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from items.models import Item


User = get_user_model()


SEED_ITEMS = [
    {
        "title": "Black Leather Wallet",
        "category": "bags",
        "status": "lost",
        "location": "Main Library - Quiet Reading Room",
        "contact": "Please call campus security at +1-555-302-1100",
        "description": "Wallet with university ID, two credit cards, and a small amount of cash. Initials BM on the inside.",
        "days_ago": 2,
    },
    {
        "title": "Silver MacBook Air 13”",
        "category": "electronics",
        "status": "found",
        "location": "Innovation Hub - Conference Room B",
        "contact": "Email beris@example.com to arrange pickup.",
        "description": "Device had stickers for Django, React, and PyCon. Logged out, discovered after a meetup.",
        "days_ago": 4,
    },
    {
        "title": "Set of Apartment Keys",
        "category": "keys",
        "status": "lost",
        "location": "Downtown coffee shop - Oak & 5th",
        "contact": "Text +1-555-901-7770 if found.",
        "description": "Three brass keys on a leather keychain with a small flashlight. Lost during morning commute.",
        "days_ago": 9,
    },
    {
        "title": "Blue North Face Backpack",
        "category": "bags",
        "status": "found",
        "location": "Campus Gym - Locker Room",
        "contact": "Stored at reception desk until Friday.",
        "description": "Contains sports gear and a math notebook labelled 'Calculus III'.",
        "days_ago": 6,
    },
    {
        "title": "Vintage Omega Wristwatch",
        "category": "jewelry",
        "status": "returned_to_owner",
        "location": "City Arts Center Auditorium",
        "contact": "Returned at the lost and found desk.",
        "description": "Watch with leather strap. Item has already been reunited with owner thanks to this platform.",
        "days_ago": 14,
    },
    {
        "title": "Intro to Algorithms Textbook",
        "category": "books",
        "status": "lost",
        "location": "Computer Science Building - Room 204",
        "contact": "Leave at the CS department office if found.",
            "description": "Book with many annotations and sticky notes. Cover has name 'Sekatawa Eric'.",
        "days_ago": 5,
    },
    {
        "title": "USB-C Portable Charger",
        "category": "electronics",
        "status": "found",
        "location": "Downtown bus line 18",
        "contact": "Message via the lost & found inbox.",
        "description": "Anker brand power bank, 20,000 mAh. Found on the evening commute.",
        "days_ago": 8,
    },
    {
        "title": "Set of Workshop Tools",
        "category": "other",
        "status": "lost",
        "location": "Makerspace Garage",
        "contact": "Notify makerspace staff, toolbox labelled 'BM Projects'.",
        "description": "Tool roll containing precision screwdrivers, soldering iron, and pliers.",
        "days_ago": 12,
    },
    {
        "title": "Golden Retriever Collar Tag",
        "category": "other",
        "status": "found",
        "location": "Riverside Park - Dog Run",
        "contact": "Call +1-555-234-8899 to verify pet details.",
        "description": "Custom engraved tag for a dog named 'Pixel'.",
        "days_ago": 1,
    },
    {
        "title": "Wireless Earbuds Case",
        "category": "electronics",
        "status": "lost",
        "location": "Physics Building - Lecture Hall 3",
        "contact": "Reply in app or drop at lecture hall podium.",
        "description": "Black Sony WF-1000XM5 case, missing left earbud.",
        "days_ago": 3,
    },
    {
        "title": "Passport - Nigerian",
        "category": "documents",
        "status": "lost",
        "location": "International Student Office",
        "contact": "Urgent: call +1-555-870-4412 if located.",
            "description": "Passport belonging to Sekatawa Eric, lost during paperwork submission.",
        "days_ago": 16,
    },
    {
        "title": "Charcoal Grey Hoodie",
        "category": "clothing",
        "status": "found",
        "location": "Residence Hall Laundry Room",
        "contact": "Hanging on lost & found rack near machines.",
        "description": "Medium hoodie with embroidered initials 'B.M.' inside the collar.",
        "days_ago": 7,
    },
]


class Command(BaseCommand):
    help = "Seed representative lost & found items attributed to Beris Martin."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Remove previously seeded sample items before creating new ones.",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=len(SEED_ITEMS),
            help="Number of items to seed (defaults to full curated set).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        seed_payload = SEED_ITEMS[:count]
        if not seed_payload:
            self.stdout.write(self.style.WARNING("No seed items selected. Nothing to do."))
            return

        user, created = User.objects.get_or_create(
            username="sekatawa.eric",
            defaults={
                "first_name": "Sekatawa",
                "last_name": "Eric",
                "email": "eric+lostfound@example.com",
            },
        )
        if created:
            user.set_password("changeme123")
            user.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS("Created user 'sekatawa.eric' with temporary password 'changeme123'."))
        else:
            self.stdout.write(self.style.HTTP_INFO("Using existing user 'sekatawa.eric'."))

        curated_titles = {item["title"] for item in seed_payload}
        if options["flush"]:
            deleted, _ = Item.objects.filter(user=user, title__in=curated_titles).delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} previously seeded items."))

        created_items = 0
        skipped_items = 0
        now = timezone.now()
        for data in seed_payload:
            target_datetime = now - timedelta(days=data["days_ago"])
            defaults = {
                "description": data["description"],
                "category": data["category"],
                "status": data["status"],
                "location_lost_found": data["location"],
                "date_lost_found": target_datetime,
                "contact_info": data["contact"],
                "is_active": data["status"] in {"lost", "found"},
            }
            item, item_created = Item.objects.get_or_create(
                title=data["title"],
                user=user,
                defaults=defaults,
            )
            if item_created:
                created_items += 1
            else:
                skipped_items += 1
                # Optionally refresh existing data
                for field, value in defaults.items():
                    setattr(item, field, value)
                item.save()

            Item.objects.filter(pk=item.pk).update(
                created_at=target_datetime,
                updated_at=target_datetime,
            )

        summary = f"Seed complete: {created_items} created, {skipped_items} refreshed/kept."
        self.stdout.write(self.style.SUCCESS(summary))
        self.stdout.write(self.style.HTTP_INFO("You can now add images or tweak details via the admin or UI."))

