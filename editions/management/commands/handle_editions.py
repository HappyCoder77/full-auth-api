from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management.base import OutputWrapper
from django.core.management.color import no_style
from collection_manager.models import Collection
from editions.models import Edition, Pack, Sticker
from django.core.exceptions import ObjectDoesNotExist, ValidationError


class Command(BaseCommand):
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            dest="operation", help="Operation to perform"
        )

        create_parser = subparsers.add_parser("create")
        create_parser.add_argument(
            "--collection",
            type=int,
            required=True,
            help="Collection ID for creating new edition",
        )
        create_parser.add_argument(
            "--circulation",
            type=int,
            required=True,
            help="Number of copies for the edition",
        )

        delete_parser = subparsers.add_parser("delete")
        delete_parser.add_argument("edition_id", type=int, help="Edition ID to delete")

    def handle(self, *args, **options):
        operation = options["operation"]

        if operation == "create":
            return self.create_edition(options)
        elif operation == "delete":
            return self.delete_edition(options)

    def create_edition(self, options):
        """
        Creates a new edition for a given collection with specified circulation.
        Args:
            options (dict): A dictionary containing the following keys:
                - collection (int): The ID of the collection for which the edition is to be created.
                - circulation (int): The circulation number for the new edition.
        Returns:
            None
        Raises:
            ObjectDoesNotExist: If the collection with the specified ID does not exist.
        Prompts:
            Asks the user for confirmation before proceeding with the edition creation.
        Outputs:
            Writes progress and success messages to stdout.
        Sintax:
            python manage.py handle_editions create --collection <collection_id> --circulation<circulation>
        """

        try:
            collection = Collection.objects.get(id=options["collection"])

            edition = Edition(
                collection=collection, circulation=Decimal(str(options["circulation"]))
            )

            try:
                edition.full_clean()
            except ValidationError as e:
                self.stdout.write(self.style.ERROR("\nValidation error:"))
                # Handle different types of validation errors
                if hasattr(e, "message_dict"):
                    # Field-specific errors
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            self.stdout.write(self.style.ERROR(f"- {field}: {error}"))
                else:
                    # General errors
                    for error in e.messages:
                        self.stdout.write(self.style.ERROR(f"- {error}"))

                readiness = collection.is_ready_for_edition()

                if not readiness["ready"]:
                    issues = readiness["issues"]

                    if issues["coordinates_without_images"] > 0:
                        total = collection.album_template.coordinates.count()
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nAlbum template has {issues['coordinates_without_images']} of {total} coordinates without images."
                            )
                        )

                    if issues["undefined_standard_prizes"] > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nCollection has {issues['undefined_standard_prizes']} undefined standard prizes."
                            )
                        )

                    if issues["undefined_surprise_prizes"] > 0:
                        self.stdout.write(
                            self.style.WARNING(
                                f"\nCollection has {issues['undefined_surprise_prizes']} undefined surprise prizes."
                            )
                        )

                return

            self.stdout.write(f"\nCreating new edition for:")
            self.stdout.write(f"Collection: {collection.album_template.name}")
            self.stdout.write(f"Promotion: {collection.promotion}")
            self.stdout.write(f"Circulation: {options['circulation']}")

            if input("\nProceed with edition creation? [yes/N]: ").lower() != "yes":
                self.stdout.write(self.style.WARNING("Operation cancelled"))
                return

            # Create edition
            self.stdout.write("Creating edition...")

            try:
                edition.save()
                # Show progress for related objects
                boxes = edition.boxes.count()
                packs = Pack.objects.filter(box__edition=edition).count()
                stickers = Sticker.objects.filter(pack__box__edition=edition).count()

                total_objects = boxes + packs + stickers

                self.stdout.write("Objects created:")
                self.stdout.write(f"- Boxes: {boxes}")
                self.stdout.write(f"- Packs: {packs}")
                self.stdout.write(f"- Stickers: {stickers}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nEdition created successfully:"
                        f"\nID: {edition.id}"
                        f"\nCollection: {edition.collection.theme.name}"
                        f"\nCirculation: {edition.circulation}"
                        f"\nTotal objects: {total_objects}"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"\nError creating edition: {str(e)}")
                )
                self.stdout.write(
                    self.style.WARNING(
                        "The operation was rolled back and no data was created."
                    )
                )

        except ObjectDoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f"Collection with ID {options['collection']} does not exist"
                )
            )

    def delete_edition(self, options):
        edition_id = options["edition_id"]

        try:
            edition = Edition.objects.get(id=options["edition_id"])

            related_counts = {
                "boxes": edition.boxes.count(),
                "packs": Pack.objects.filter(box__edition=edition).count(),
                "stickers": Sticker.objects.filter(pack__box__edition=edition).count(),
            }

            self.stdout.write(f"\nEdition to delete:")
            self.stdout.write(f"ID: {edition.id}")
            self.stdout.write(f"Collection: {edition.collection.theme.name}")
            self.stdout.write(f"Promotion: {edition.collection.promotion}")
            self.stdout.write(f"Circulation: {edition.circulation}")
            self.stdout.write("\nRelated objects to be deleted:")
            self.stdout.write(f"- Boxes: {related_counts['boxes']}")
            self.stdout.write(f"- Packs: {related_counts['packs']}")
            self.stdout.write(f"- Stickers: {related_counts['stickers']}")

            if (
                input("\nAre you sure you want to delete this edition? [y/N]: ").lower()
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
