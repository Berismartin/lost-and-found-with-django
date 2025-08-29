from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message, Item, Comment, Notification
# from .models import Item, Comment, Notification # Assuming Notification model exists
from django.contrib.auth.models import User
import re



# Create your views here.
from django.http import HttpResponse
# from django.template import loader

def home(request):
    return HttpResponse("Welcome to the Lost and Found Home Page!")
# @login_required
# def inbox_view(request):
#     conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
#     return render(request, 'inbox.html', {'conversations': conversations})

@login_required
def inbox_view(request):
    conversations = request.user.conversations.all()
    return render(request, "inbox.html", {"conversations": conversations})




@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('inbox') 

    messages = conversation.messages.all()
    return render(request, 'conversation.html', {
        'conversation': conversation,
        'messages': messages,
    })
    

@login_required
def send_message(request, conversation_id):
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user not in conversation.participants.all():
            return redirect('inbox')
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
        return redirect('conversation_detail', conversation_id=conversation.id)
    return redirect('inbox')


@login_required
def add_comment(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                item=item,
                user=request.user,
                content=content
            )
            tag_user_notification(comment)
            
    return redirect('item_detail', item_id=item_id)


@login_required
def add_reply(request, item_id, parent_id):
    item = get_object_or_404(Item, id=item_id)
    parent_comment = get_object_or_404(Comment, id=parent_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                item=item,
                user=request.user,
                parent=parent_comment,
                content=content
            )
            tag_user_notification(comment)
            
    return redirect('item_detail', item_id=item_id)


def tag_user_notification(comment):
    usernames = re.findall(r'@(\w+)', comment.content)
    
    for username in usernames:
        try:
            
            tagged_user = User.objects.get(username=username)
            
            if tagged_user != comment.user:
                Notification.objects.create(
                    user=tagged_user,
                    message=f"You were tagged by {comment.user.username} in a comment on '{comment.item.name}'."
                )
        except User.DoesNotExist:
            continue