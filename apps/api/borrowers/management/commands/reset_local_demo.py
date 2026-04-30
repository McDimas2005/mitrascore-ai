from pathlib import Path
import shutil

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Reset the local demo database and reseed starter MitraScore AI data."

    def add_arguments(self, parser):
        parser.add_argument("--yes", action="store_true", help="Required confirmation flag.")
        parser.add_argument("--keep-media", action="store_true", help="Do not delete uploaded local media files.")
        parser.add_argument("--skip-migrate", action="store_true", help="Skip running migrations after flush.")

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("reset_local_demo is blocked when DEBUG=False.")
        if not options["yes"]:
            raise CommandError("Refusing to reset. Re-run with --yes for local demo data reset.")

        verbosity = options.get("verbosity", 1)
        media_root = Path(settings.MEDIA_ROOT)

        if not options["keep_media"] and media_root.exists():
            shutil.rmtree(media_root)
            self.stdout.write(f"Deleted local media: {media_root}")

        self.stdout.write("Flushing database data...")
        call_command("flush", interactive=False, verbosity=verbosity)

        if not options["skip_migrate"]:
            self.stdout.write("Applying migrations...")
            call_command("migrate", interactive=False, verbosity=verbosity)

        self.stdout.write("Seeding starter demo data...")
        call_command("seed_demo", verbosity=verbosity)

        self.stdout.write(self.style.SUCCESS("Local demo reset complete."))
