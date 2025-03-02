from django.core.management.base import BaseCommand
from editions.models import Edition, Box, Pack, Sticker
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("operation", type=str, help="create/update/delete")
        parser.add_argument("edition_id", type=int, help="Edition ID")

    def handle(self, *args, **options):
        operation = options["operation"]
        edition_id = options["edition_id"]

        try:
            edition = Edition.objects.get(id=edition_id)

            if operation == "delete":
                # Count related objects before deletion
                related_counts = {
                    "boxes": edition.boxes.count(),
                    "packs": Pack.objects.filter(box__edition=edition).count(),
                    "stickers": Sticker.objects.filter(
                        pack__box__edition=edition
                    ).count(),
                }

                self.stdout.write(f"\nEdition to delete:")
                self.stdout.write(f"ID: {edition.id}")
                self.stdout.write(f"Collection: {edition.collection.name}")
                self.stdout.write(f"Promotion: {edition.promotion}")
                self.stdout.write(f"Circulation: {edition.circulation}")
                self.stdout.write("\nRelated objects to be deleted:")
                self.stdout.write(f"- Boxes: {related_counts['boxes']}")
                self.stdout.write(f"- Packs: {related_counts['packs']}")
                self.stdout.write(f"- Stickers: {related_counts['stickers']}")

                if (
                    input(
                        "\nAre you sure you want to delete this edition? [y/N]: "
                    ).lower()
                    != "y"
                ):
                    self.stdout.write(self.style.WARNING("Operation cancelled"))
                    return

                edition.delete()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nEdition {edition_id} successfully deleted with:"
                        f"\n- {related_counts['boxes']} boxes"
                        f"\n- {related_counts['packs']} packs"
                        f"\n- {related_counts['stickers']} stickers"
                    )
                )

        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Edition with ID {edition_id} does not exist")
            )
