from django.test import TestCase
from django.urls import reverse

from accounts.models import Alumni


class AlumniRecommendationTests(TestCase):

    def setUp(self):
        self.alumni_a = Alumni.objects.create(
            register_number="A1001",
            full_name="John Smith",
            company="TechNova",
            position="Software Engineer",
            batch=2020,
        )

        self.alumni_b = Alumni.objects.create(
            register_number="B1001",
            full_name="John Smith",
            company="CloudWorks",
            position="Data Analyst",
            batch=2021,
        )

        self.alumni_c = Alumni.objects.create(
            register_number="C1001",
            full_name="Jane Doe",
            company="OpenAI",
            position="Product Manager",
            batch=2022,
        )

        self.alumni_a.knn_similar_alumni = "B1001, C1001"
        self.alumni_a.recommended_alumni = "B1001, C1001"
        self.alumni_a.save()

    def test_similar_alumni_view_uses_register_numbers(self):
        response = self.client.get(
            reverse("similar_alumni", args=[self.alumni_a.register_number])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alumni_b.full_name)
        self.assertContains(response, self.alumni_c.full_name)

    def test_recommended_alumni_view_uses_register_numbers(self):
        response = self.client.get(
            reverse("recommended_alumni", args=[self.alumni_a.register_number])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alumni_b.full_name)
        self.assertContains(response, self.alumni_c.full_name)

    def test_directory_view_shows_all_alumni(self):
        response = self.client.get(reverse("directory"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.alumni_a.full_name)
        self.assertContains(response, self.alumni_b.full_name)
        self.assertContains(response, self.alumni_c.full_name)

    def test_directory_view_shows_live_statistics(self):
        response = self.client.get(reverse("directory"))

        self.assertEqual(response.context["total_alumni"], 3)
        self.assertEqual(response.context["active_alumni"], 3)
        self.assertEqual(response.context["total_batches"], 3)
        self.assertEqual(response.context["total_companies"], 3)


class AlumniLoginTests(TestCase):

    def setUp(self):
        self.alumni = Alumni.objects.create(
            register_number="BU241937",
            full_name="Test Alumni",
        )

    def test_login_accepts_the_username_field_and_counts_success(self):
        response = self.client.post(
            reverse("login"),
            {"username": "BU241937", "password": "shc"},
        )

        self.assertRedirects(response, reverse("home"))
        self.alumni.refresh_from_db()
        self.assertEqual(self.alumni.successful_logins, 1)

    def test_login_page_uses_live_alumni_count(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.context["total_members"], 1)
        self.assertEqual(response.context["total_logins"], 0)
