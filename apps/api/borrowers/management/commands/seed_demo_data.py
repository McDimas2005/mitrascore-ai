from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Idempotently seed MitraScore AI demo users and starter demo cases."

    def handle(self, *args, **options):
        call_command("seed_demo", verbosity=options.get("verbosity", 1))
