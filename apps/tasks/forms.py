from django import forms

from apps.projects.models import Project

from .models import Comment, Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "description", "project", "assigned_to", "priority", "status", "deadline"]
        widgets = {"deadline": forms.DateTimeInput(attrs={"type": "datetime-local"})}

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["project"].queryset = Project.objects.filter(company=company)
            self.fields["assigned_to"].queryset = company.members.filter(is_active=True)
        self.fields["assigned_to"].required = False


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Write a comment…"})}
