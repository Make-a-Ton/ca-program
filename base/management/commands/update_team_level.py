import csv
from django.core.management.base import BaseCommand
from makeaton.models import Team


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
                    phone = row['Team Leader Phone Number']
                    classification = row['Classification']
                    score = row['Score']
                    reason = row['Reason']

                    # Fetch the team member by email
                    try:
                        team = Team.objects.get(leader_phone__contains=phone)
                        team.level = classification  # Update the level of expertise
                        team.llm_score = score
                        team.llm_review = reason
                        team.save()
                        self.stdout.write(self.style.SUCCESS(
                            f"Email: {phone}, Classification: {classification}, Score: {score}, Reason: {reason}"))


                    except Team.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Team member with phone {phone} not found"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"An error occurred: {phone} {str(e)}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File {csv_file_path} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {str(e)}"))
