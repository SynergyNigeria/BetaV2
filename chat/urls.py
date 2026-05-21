from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_router, name='chat'),
    path('inbox/', views.chat_detail, name='chat_detail'),
    path('admin/list/', views.chat_list, name='chat_list'),
    path('admin/<int:session_id>/', views.admin_chat_detail, name='admin_chat_detail'),
    path('send/', views.send_message, name='send_message'),
    path('poll/', views.poll_messages, name='poll_messages'),
]
