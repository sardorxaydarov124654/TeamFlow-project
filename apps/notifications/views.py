from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "notifications/list.html", {"notifications": notifications})


@login_required
def notification_mark_read_view(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if request.method == "POST":
        notification.is_read = True
        notification.save(update_fields=["is_read"])
    return redirect("notifications:list")


@login_required
def notifications_mark_all_read_view(request):
    if request.method == "POST":
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, f"Marked {updated} notification(s) as read.")
    return redirect("notifications:list")
