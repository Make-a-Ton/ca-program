import csv
from django.core.management.base import BaseCommand
from makeaton.models import TeamMember


class Command(BaseCommand):
    help = 'Update team member level from a CSV file based on the email.'

    def add_arguments(self, parser):
        # Argument to specify the path of the CSV file
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        csv_file_path = kwargs['csv_file']
        count = 0
        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    try:
                        email = row['email']
                        count += 1
                        TeamMember.objects.filter(email=email).update(college_name=row['College Names'])
                        self.stdout.write(self.style.SUCCESS(f"Updated {email}'s level to {row['College Names']}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An error occurred: {email} {str(e)}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File {csv_file_path} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"Updated {count} records"))

