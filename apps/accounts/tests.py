from django.test import TestCase
from rest_framework.test import APIClient

from apps.companies.models import Company

from .models import User


class AuthFlowTests(TestCase):
    def test_register_creates_user_and_company(self):
        client = APIClient()
        resp = client.post(
            "/api/auth/register/",
            {
                "email": "Owner@Example.com",
                "password": "StrongPass123",
                "company_name": "Acme Inc",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertIn("access", resp.data)
        user = User.objects.get(email="owner@example.com")  # normalized to lowercase
        self.assertEqual(user.role, User.Role.MANAGER)
        self.assertIsNotNone(user.company)
        self.assertEqual(user.company.owner, user)

    def test_login_is_case_insensitive_on_email(self):
        client = APIClient()
        client.post(
            "/api/auth/register/",
            {"email": "owner@example.com", "password": "StrongPass123", "company_name": "Acme"},
            format="json",
        )
        resp = client.post(
            "/api/auth/login/",
            {"email": "OWNER@EXAMPLE.COM", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_login_rejects_wrong_password(self):
        client = APIClient()
        client.post(
            "/api/auth/register/",
            {"email": "owner@example.com", "password": "StrongPass123", "company_name": "Acme"},
            format="json",
        )
        resp = client.post(
            "/api/auth/login/",
            {"email": "owner@example.com", "password": "WrongPassword"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_token_refresh_flow(self):
        client = APIClient()
        resp = client.post(
            "/api/auth/register/",
            {"email": "owner@example.com", "password": "StrongPass123", "company_name": "Acme"},
            format="json",
        )
        refresh = resp.data["refresh"]
        resp2 = client.post("/api/auth/token/refresh/", {"refresh": refresh}, format="json")
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("access", resp2.data)


class RolePermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        resp = self.client.post(
            "/api/auth/register/",
            {"email": "manager@a.com", "password": "StrongPass123", "company_name": "Company A"},
            format="json",
        )
        self.manager_token = resp.data["access"]
        self.company = Company.objects.get(name="Company A")

        self.employee = User.objects.create_user(
            email="employee@a.com", password="StrongPass123", role=User.Role.EMPLOYEE
        )
        self.employee.company = self.company
        self.employee.save()

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_manager_can_invite_member(self):
        resp = self.client.post(
            "/api/company/members/invite/",
            {"email": "new@a.com", "role": "employee"},
            format="json",
            **self._auth(self.manager_token),
        )
        self.assertEqual(resp.status_code, 201)

    def test_employee_cannot_invite_member(self):
        login = self.client.post(
            "/api/auth/login/",
            {"email": "employee@a.com", "password": "StrongPass123"},
            format="json",
        )
        emp_token = login.data["access"]
        resp = self.client.post(
            "/api/company/members/invite/",
            {"email": "new@a.com", "role": "employee"},
            format="json",
            **self._auth(emp_token),
        )
        self.assertEqual(resp.status_code, 403)


class TenantIsolationTests(TestCase):
    """The single most important security test in the whole TZ (see #19, #24)."""

    def setUp(self):
        self.client = APIClient()

        resp_a = self.client.post(
            "/api/auth/register/",
            {"email": "owner@a.com", "password": "StrongPass123", "company_name": "Company A"},
            format="json",
        )
        self.token_a = resp_a.data["access"]

        resp_b = self.client.post(
            "/api/auth/register/",
            {"email": "owner@b.com", "password": "StrongPass123", "company_name": "Company B"},
            format="json",
        )
        self.token_b = resp_b.data["access"]

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_company_a_cannot_see_company_b_projects(self):
        create = self.client.post(
            "/api/projects/",
            {"name": "Secret Project B"},
            format="json",
            **self._auth(self.token_b),
        )
        self.assertEqual(create.status_code, 201)
        project_b_id = create.data["id"]

        resp = self.client.get(f"/api/projects/{project_b_id}/", **self._auth(self.token_a))
        self.assertEqual(resp.status_code, 404)

        listing = self.client.get("/api/projects/", **self._auth(self.token_a))
        self.assertEqual(listing.data["count"], 0)

    def test_company_a_cannot_see_company_b_members(self):
        resp = self.client.get("/api/company/members/", **self._auth(self.token_a))
        emails = [m["email"] for m in resp.data["results"]]
        self.assertNotIn("owner@b.com", emails)
