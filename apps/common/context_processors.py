def unread_notifications(request):
    """Adds the current user's unread notification count to every template."""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {"unread_notification_count": count}
    return {}
