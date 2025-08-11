from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication URLs
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    # Account Management URLs
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("settings/", views.settings_view, name="settings"),
    path("support/", views.support_view, name="support"),
    # Profile Management
    path("profile/", views.profile_view, name="profile"),
    path("profile/update/", views.profile_update_view, name="profile_update"),
    # Notifications
    path("notifications/", views.notifications_view, name="notifications"),
    path(
        "notifications/<int:notification_id>/mark-read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
]
