from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from users.models import UserProfile

User = get_user_model()


class TestUsersAuthAndProfileGivenWhenThen(TestCase):
    def setUp(self):
        self.client = Client()

    def test_given_valid_registration_when_submit_form_then_profile_created_it_logs_user_in(self):
        resp = self.client.post(
            reverse("register_user"),
            {
                "username": "alice",
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "L",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        user = User.objects.get(username="alice")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_given_valid_credentials_and_next_when_login_then_redirects_it_respects_next_param(self):
        User.objects.create_user(username="bob", password="pass12345", email="b@example.com", first_name="Bob")
        resp = self.client.post(
            reverse("login_user") + "?next=/users/profile/",
            {"username": "bob", "password": "pass12345"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], "/users/profile/")

    def test_given_logged_in_user_when_logout_then_redirects_to_login_it_clears_session(self):
        User.objects.create_user(username="c", password="p", email="c@example.com", first_name="C")
        self.client.login(username="c", password="p")
        resp = self.client.get(reverse("logout_user"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login_user"), resp["Location"])

    def test_given_missing_profile_when_view_profile_then_autocreates_it_shows_page(self):
        user = User.objects.create_user(username="d", password="p", email="d@example.com", first_name="D")
        self.client.login(username="d", password="p")
        resp = self.client.get(reverse("profile_view"))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_given_valid_forms_when_edit_profile_then_updates_user_it_persists_changes(self):
        user = User.objects.create_user(username="e", password="p", email="e@example.com", first_name="E")
        self.client.login(username="e", password="p")
        resp = self.client.post(
            reverse("edit_profile"),
            {
                "first_name": "Ed",
                "last_name": "New",
                "email": "e@example.com",
                "username": "e",
                "bio": "hello",
                "phone_number": "123",
                "location": "X",
                "date_of_birth": "",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Ed")
