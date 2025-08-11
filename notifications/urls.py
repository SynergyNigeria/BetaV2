from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notifications_view, name="notifications"),
    path(
        "<int:notification_id>/mark-read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
]
