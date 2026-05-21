from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from .models import ChatSession, ChatMessage


@login_required
def chat_router(request):
    """Route: admin -> chat list, user -> their chat detail."""
    if request.user.is_staff:
        return redirect('chat:chat_list')
    return redirect('chat:chat_detail')


@login_required
def chat_detail(request):
    """User's chat page with admin support."""
    if request.user.is_staff:
        return redirect('chat:chat_list')

    session, _ = ChatSession.objects.get_or_create(user=request.user)
    # Mark admin messages as read
    session.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages = session.messages.order_by('timestamp')
    return render(request, 'chat/chat_detail.html', {
        'session': session,
        'messages': messages,
    })


@login_required
@staff_member_required
def chat_list(request):
    """Admin view: list all user chat sessions."""
    sessions = ChatSession.objects.select_related('user').order_by('-updated_at')
    # Annotate unread count per session
    from django.db.models import Count, Q
    sessions_with_unread = []
    for s in sessions:
        unread = s.messages.filter(is_read=False).exclude(sender__is_staff=True).count()
        last_msg = s.messages.last()
        sessions_with_unread.append({
            'session': s,
            'unread': unread,
            'last_message': last_msg,
        })
    return render(request, 'chat/chat_list.html', {
        'sessions_data': sessions_with_unread,
    })


@login_required
@staff_member_required
def admin_chat_detail(request, session_id):
    """Admin view: reply to a specific user's chat."""
    session = get_object_or_404(ChatSession, id=session_id)
    # Mark user messages as read
    session.messages.filter(is_read=False).exclude(sender__is_staff=True).update(is_read=True)

    messages = session.messages.order_by('timestamp')
    return render(request, 'chat/admin_chat_detail.html', {
        'session': session,
        'messages': messages,
    })


@login_required
@require_POST
def send_message(request):
    """Send a message (user or admin)."""
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    if request.user.is_staff:
        session_id = request.POST.get('session_id')
        session = get_object_or_404(ChatSession, id=session_id)
    else:
        session, _ = ChatSession.objects.get_or_create(user=request.user)

    msg = ChatMessage.objects.create(
        session=session,
        sender=request.user,
        content=content,
    )
    # Touch session updated_at
    session.save()

    return JsonResponse({
        'id': msg.id,
        'sender': msg.sender.username,
        'is_staff': msg.sender.is_staff,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%b %d, %H:%M'),
    })


@login_required
def poll_messages(request):
    """Return messages newer than a given message id for polling."""
    last_id = request.GET.get('last_id', 0)
    session_id = request.GET.get('session_id')

    try:
        last_id = int(last_id)
    except (ValueError, TypeError):
        last_id = 0

    if request.user.is_staff:
        session = get_object_or_404(ChatSession, id=session_id)
    else:
        session = get_object_or_404(ChatSession, user=request.user)

    new_messages = session.messages.filter(id__gt=last_id).order_by('timestamp')

    # Mark incoming messages as read
    if request.user.is_staff:
        new_messages.filter(is_read=False).exclude(sender__is_staff=True).update(is_read=True)
    else:
        new_messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    data = [{
        'id': m.id,
        'sender': m.sender.username,
        'is_staff': m.sender.is_staff,
        'content': m.content,
        'timestamp': m.timestamp.strftime('%b %d, %H:%M'),
    } for m in new_messages]

    return JsonResponse({'messages': data})

