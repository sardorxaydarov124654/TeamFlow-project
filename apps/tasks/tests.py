from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.companies.models import Company
from apps.notifications.models import Notification
from apps.projects.models import Project

from .models import Task


class TaskAndCommentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        resp = self.client.post(
            "/api/auth/register/",
            {"email": "manager@a.com", "password": "StrongPass123", "company_name": "Company A"},
            format="json",
        )
        self.manager_token = resp.data["access"]
        self.company = Company.objects.get(name="Company A")
        self.manager = User.objects.get(email="manager@a.com")

        self.employee = User.objects.create_user(
            email="employee@a.com", password="StrongPass123", role=User.Role.EMPLOYEE
        )
        self.employee.company = self.company
        self.employee.save()

        self.project = Project.objects.create(
            name="Website Redesign", company=self.company, owner=self.manager
        )

    def _auth(self, token):
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def _login(self, email, password="StrongPass123"):
        resp = self.client.post(
            "/api/auth/login/", {"email": email, "password": password}, format="json"
        )
        return resp.data["access"]

    def test_manager_can_create_and_assign_task(self):
        resp = self.client.post(
            "/api/tasks/",
            {"title": "Build homepage", "project": self.project.id, "assigned_to": self.employee.id},
            format="json",
            **self._auth(self.manager_token),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Notification.objects.filter(user=self.employee, type="task_assigned").exists()
        )

    def test_employee_cannot_create_task(self):
        emp_token = self._login("employee@a.com")
        resp = self.client.post(
            "/api/tasks/",
            {"title": "Not allowed", "project": self.project.id},
            format="json",
            **self._auth(emp_token),
        )
        self.assertEqual(resp.status_code, 403)

    def test_employee_can_change_status_of_own_task(self):
        task = Task.objects.create(
            title="Fix bug",
            project=self.project,
            company=self.company,
            assigned_to=self.employee,
            created_by=self.manager,
        )
        emp_token = self._login("employee@a.com")
        resp = self.client.patch(
            f"/api/tasks/{task.id}/",
            {"status": "in_progress"},
            format="json",
            **self._auth(emp_token),
        )
        self.assertEqual(resp.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "in_progress")
        self.assertTrue(
            Notification.objects.filter(user=self.manager, type="task_status_changed").exists()
        )

    def test_comment_creates_notification_for_other_party(self):
        task = Task.objects.create(
            title="Fix bug",
            project=self.project,
            company=self.company,
            assigned_to=self.employee,
            created_by=self.manager,
        )
        emp_token = self._login("employee@a.com")
        resp = self.client.post(
            f"/api/tasks/{task.id}/comments/",
            {"body": "Almost done"},
            format="json",
            **self._auth(emp_token),
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(
            Notification.objects.filter(user=self.manager, type="comment_added").exists()
        )

    def test_task_filtering_and_search(self):
        Task.objects.create(
            title="Urgent fix", project=self.project, company=self.company,
            priority="urgent", status="todo", created_by=self.manager,
        )
        Task.objects.create(
            title="Low priority polish", project=self.project, company=self.company,
            priority="low", status="done", created_by=self.manager,
        )
        resp = self.client.get(
            "/api/tasks/?priority=urgent", **self._auth(self.manager_token)
        )
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["title"], "Urgent fix")

        resp = self.client.get(
            "/api/tasks/?search=polish", **self._auth(self.manager_token)
        )
        self.assertEqual(resp.data["count"], 1)
