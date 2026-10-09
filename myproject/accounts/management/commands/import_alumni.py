import os
from datetime import date, datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from openpyxl import load_workbook

from accounts.models import Alumni


class Command(BaseCommand):

    help = "Import alumni data from Excel"

    def find_excel_file(self):
        project_root = Path(settings.BASE_DIR)
        candidates = [
            project_root / "alumni_portal_46_students.xlsx",
            project_root / "alumni_portal_46_students.xlxs.xlsx",
            project_root / "alumni.xlsx",
            Path.home() / "Downloads" / "alumni_portal_46_students.xlsx",
            Path.home() / "Downloads" / "alumni_portal_46_students.xlxs.xlsx",
        ]

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        pattern_files = list(project_root.glob("*.xlsx")) + list(project_root.glob("*.xls"))
        if pattern_files:
            return str(pattern_files[0])

        downloads = Path.home() / "Downloads"
        if downloads.exists():
            matching = sorted(downloads.glob("*alumni*.xlsx")) + sorted(downloads.glob("*alumni*.xls"))
            if matching:
                return str(matching[0])

        return None

    def normalize_date(self, value):
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            try:
                return datetime.fromisoformat(cleaned).date()
            except ValueError:
                try:
                    return date.fromisoformat(cleaned)
                except ValueError:
                    return None
        return None

    def handle(self, *args, **kwargs):
        file_path = self.find_excel_file()

        if not file_path:
            self.stdout.write(
                self.style.ERROR(
                    "Excel file not found!"
                )
            )
            self.stdout.write(
                "Place the workbook in the project folder or Downloads folder."
            )
            return

        self.stdout.write(f"Using Excel file at: {file_path}")

        try:
            workbook = load_workbook(file_path, data_only=True)
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Could not open Excel file: {exc}"))
            return

        sheet_name = None
        for name in workbook.sheetnames:
            lower = name.lower()
            if "alumni" in lower or "dataset" in lower:
                sheet_name = name
                break

        if not sheet_name:
            self.stdout.write(self.style.ERROR("No alumni dataset sheet found."))
            self.stdout.write(f"Available sheets: {workbook.sheetnames}")
            return

        worksheet = workbook[sheet_name]
        rows = list(worksheet.iter_rows(min_row=2, values_only=True))

        self.stdout.write(f"Found {len(rows)} records in Excel sheet '{sheet_name}'.")

        imported = 0
        updated = 0

        for row in rows:
            if not row or all(cell is None or str(cell).strip() == "" for cell in row):
                continue

            if len(row) < 9:
                continue

            full_name, register_number, _branch, date_of_birth, position, batch_value, email, phone, company = row[:9]

            if not register_number or not full_name:
                continue

            register_number = str(register_number).strip()
            full_name = str(full_name).strip()

            if not register_number or not full_name:
                continue

            dob = self.normalize_date(date_of_birth)
            batch = int(batch_value) if batch_value not in (None, "", " ") else 2027

            alumnus, created = Alumni.objects.update_or_create(
                register_number=register_number,
                defaults={
                    "full_name": full_name,
                    "date_of_birth": dob,
                    "email": str(email).strip() if email else "",
                    "phone": str(phone).strip() if phone else "",
                    "batch": batch,
                    "company": str(company).strip() if company else "",
                    "position": str(position).strip() if position else "",
                    "feedback": "",
                    "kmeans_cluster": None,
                    "knn_similar_alumni": "",
                    "recommended_alumni": "",
                    "sentiment_score": None,
                    "sentiment": "",
                    "location": "",
                },
            )

            if created:
                imported += 1
            else:
                updated += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("========================================"))
        self.stdout.write(self.style.SUCCESS("       ALUMNI IMPORT COMPLETED"))
        self.stdout.write(self.style.SUCCESS("========================================"))
        self.stdout.write(f"New records imported : {imported}")
        self.stdout.write(f"Existing records updated : {updated}")
        self.stdout.write(f"Total records in database : {Alumni.objects.count()}")
        self.stdout.write(self.style.SUCCESS("========================================"))