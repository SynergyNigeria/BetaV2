from django.shortcuts import render
from django.http import HttpResponse


# Notifications main view
def notifications_view(request):
    return render(request, "notifications/notifications.html")


def mark_notification_read(request, notification_id):
    return HttpResponse(f"Notification {notification_id} marked as read.")


def mark_all_notifications_read(request):
    return HttpResponse("All notifications marked as read.")
