import csv
from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from .models import TeamMember


# Custom form for CSV file upload
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


# Predefined CSV to Model Field Mapping
FIELD_MAPPING = {
    "CSV Name Column": "name",
    "CSV Email Column": "email",
    "CSV Phone Number": "phone_number",
    "CSV Approval Status": "approval_status",
    "CSV Study Level": "level_of_study",
    "CSV College": "college_name",
    # Add other field mappings as needed
}


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'approval_status', 'level_of_study', 'college_name')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv, name='import_csv'),
        ]
        return custom_urls + urls

    # View to handle CSV upload and import
    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES['csv_file']
            # Read the CSV file
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            # Iterate through each row in the CSV
            for row in reader:
                team_member = TeamMember()

                # Map the CSV columns to model fields using the predefined FIELD_MAPPING
                for csv_field, model_field in FIELD_MAPPING.items():
                    if csv_field in row:
                        setattr(team_member, model_field, row[csv_field])

                team_member.save()  # Save each mapped row to the database

            self.message_user(request, "CSV Imported successfully!")
            return HttpResponseRedirect("../")

        form = CsvImportForm()
        return render(request, "admin/csv_form.html", {"form": form})
