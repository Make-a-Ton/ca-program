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

        try:
            with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    email = row['email']
                    print(email)
                    classification = row['Classification']

                    # Fetch the team member by email
                    try:
                        team_member = TeamMember.objects.get(email=email)
                        team_member.level = classification  # Update the level of expertise
                        team_member.save()

                        self.stdout.write(self.style.SUCCESS(f"Updated {team_member.name}'s level to {classification}"))

                    except TeamMember.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Team member with email {email} not found"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An error occurred: {email} {str(e)}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File {csv_file_path} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
