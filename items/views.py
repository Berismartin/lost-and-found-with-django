import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.db import models
from .models import Item, ItemImage, Report, Comment, Conversation, Message, Notification
from .forms import ItemForm
from .forms import CommentForm
from .forms import MessageForm
from django.urls import reverse 
from django.utils import timezone
from django.db.models.functions import TruncMonth

from users.models import UserPoints
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    """Home page view displaying recent items"""
    recent_items = Item.objects.filter(is_active=True).order_by('-created_at')[:6]
    return render(request, 'items/home.html', {'recent_items': recent_items})


@login_required
def dashboard(request):
    """Dashboard with counts, statistics, and visualizations for the current user."""
    # Scope: overall + user-specific quick stats
    now = timezone.now()
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Global counts
    total_items = Item.objects.count()
    active_items = Item.objects.filter(is_active=True).count()
    status_counts = Item.objects.values('status').order_by().annotate(count=models.Count('id'))
    status_map = {s: 0 for s, _ in Item.STATUS_CHOICES}
    for row in status_counts:
        status_map[row['status']] = row['count']

    # Category distribution
    category_counts = Item.objects.values('category').order_by().annotate(count=models.Count('id'))
    category_map = {c: 0 for c, _ in Item.CATEGORY_CHOICES}
    for row in category_counts:
        category_map[row['category']] = row['count']

    # Items created per month this year
    monthly_items_qs = (
        Item.objects.filter(created_at__gte=start_of_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .order_by('month')
        .annotate(count=models.Count('id'))
    )
    monthly_labels = [row['month'].strftime('%b %Y') for row in monthly_items_qs]
    monthly_counts = [row['count'] for row in monthly_items_qs]

    # Reports
    total_reports = Report.objects.count()
    unresolved_reports = Report.objects.filter(resolved=False).count()

    # Comments
    total_comments = Comment.objects.count()

    # Messaging quick stats for user
    user_conversations = request.user.conversations.all()
    unread_messages = Message.objects.filter(conversation__in=user_conversations, is_read=False).exclude(sender=request.user).count()

    # User points
    user_points = 0
    try:
        user_points = request.user.points.points
    except Exception:
        user_points = 0

    status_labels = [label for _, label in Item.STATUS_CHOICES]
    status_keys = [key for key, _ in Item.STATUS_CHOICES]
    category_labels = [label for _, label in Item.CATEGORY_CHOICES]
    category_keys = [key for key, _ in Item.CATEGORY_CHOICES]

    status_chart = {
        'labels': status_labels,
        'data': [status_map[key] for key in status_keys],
    }
    category_chart = {
        'labels': category_labels,
        'data': [category_map[key] for key in category_keys],
    }
    monthly_chart = {
        'labels': monthly_labels,
        'data': monthly_counts,
    }
    # Scatter data of item creation dates grouped by status
    scatter_entries = (
        Item.objects.filter(created_at__isnull=False)
        .values('id', 'title', 'status', 'created_at', 'category')
        .order_by('created_at')
    )
    scatter_chart: dict[str, list[dict[str, str]]] = {}
    daily_counts: dict[str, dict[str, int]] = {}
    for entry in scatter_entries:
        created_date = entry['created_at']
        if created_date is None:
            continue
        date_key = created_date.strftime('%Y-%m-%d')
        status_key = entry['status']
        scatter_chart.setdefault(status_key, []).append({
            'date': date_key,
            'title': entry['title'],
            'category': entry['category'],
            'id': entry['id'],
        })
        day_bucket = daily_counts.setdefault(date_key, {})
        day_bucket[status_key] = day_bucket.get(status_key, 0) + 1

    majority_timeline = []
    for date_key in sorted(daily_counts.keys()):
        counts = daily_counts[date_key]
        if counts:
            dominant_status = max(counts.items(), key=lambda item: item[1])[0]
            majority_timeline.append({
                'date': date_key,
                'status': dominant_status,
                'counts': counts,
            })

    status_summary = [
        {'label': label, 'count': status_map[key]}
        for key, label in Item.STATUS_CHOICES
    ]
    category_summary = [
        {'label': label, 'count': category_map[key]}
        for key, label in Item.CATEGORY_CHOICES
    ]

    status_labels_map = dict(Item.STATUS_CHOICES)
    category_labels_map = dict(Item.CATEGORY_CHOICES)

    # Histogram data for time to resolution (in days) for returned items
    histogram_buckets = [
        (0, 1, "≤1 day"),
        (1, 3, "1-3 days"),
        (3, 7, "3-7 days"),
        (7, 14, "1-2 weeks"),
        (14, 30, "2-4 weeks"),
        (30, None, "≥1 month"),
    ]
    resolution_counts = {label: 0 for _, _, label in histogram_buckets}
    returned_items = Item.objects.filter(status='returned_to_owner')
    for item in returned_items:
        delta = item.updated_at - item.created_at
        days = delta.total_seconds() / 86400 if delta else 0
        for start, end, label in histogram_buckets:
            if end is None and days >= start:
                resolution_counts[label] += 1
                break
            if end is not None and start <= days < end:
                resolution_counts[label] += 1
                break
    histogram_data = [
        {'bucket': label, 'count': resolution_counts[label]}
        for _, _, label in histogram_buckets
    ]

    context = {
        'total_items': total_items,
        'active_items': active_items,
        'total_reports': total_reports,
        'unresolved_reports': unresolved_reports,
        'total_comments': total_comments,
        'unread_messages': unread_messages,
        'user_points': user_points,
        'status_chart': status_chart,
        'category_chart': category_chart,
        'monthly_chart': monthly_chart,
        'scatter_chart': scatter_chart,
        'status_labels_map': status_labels_map,
        'majority_timeline': majority_timeline,
        'status_summary': status_summary,
        'category_summary': category_summary,
        'histogram_data': histogram_data,
    }
    return render(request, 'items/dashboard.html', context)


def item_list(request):
    """View to display all active items with filtering and pagination"""
    items = Item.objects.filter(is_active=True)
    
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_lost_found__icontains=search_query)
        )
    category_filter = request.GET.get('category')
    if category_filter:
        items = items.filter(category=category_filter)
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    paginator = Paginator(items, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    categories = Item.CATEGORY_CHOICES
    statuses = Item.STATUS_CHOICES
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'categories': categories,
        'statuses': statuses,
    }
    return render(request, 'items/item_list.html', context)


@login_required
def create_item(request):
    """View to handle the creation of a new item post"""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            additional_images = request.FILES.getlist('additional_images')
            for i, image_file in enumerate(additional_images):
                if image_file:
                    ItemImage.objects.create(
                        item=item,
                        image=image_file,
                        order=i + 1
                    )
            image_count = len(additional_images)
            if image_count > 0:
                messages.success(request, f'Your {item.get_status_display().lower()} item "{item.title}" has been posted successfully with {image_count + (1 if item.image else 0)} images!')
            else:
                messages.success(request, f'Your {item.get_status_display().lower()} item "{item.title}" has been posted successfully!')
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm()
    return render(request, 'items/create_item.html', {'form': form})


def item_detail(request, pk):
    """View that fetches and displays a single item's details"""
    item = get_object_or_404(Item, pk=pk, is_active=True)
    is_owner = request.user.is_authenticated and item.user == request.user
    context = {
        'item': item,
        'is_owner': is_owner,
    }
    return render(request, 'items/item_detail.html',{"item": item})



@login_required
def edit_item(request, pk):
    """View to handle the form for updating an existing item"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            additional_images = request.FILES.getlist('additional_images')
            if additional_images:
                max_order = item.item_images.aggregate(
                    max_order=Max('order')
                )['max_order'] or 0
                for i, image_file in enumerate(additional_images):
                    if image_file:
                        ItemImage.objects.create(
                            item=item,
                            image=image_file,
                            order=max_order + i + 1
                        )
                messages.success(request, f'Your item "{item.title}" has been updated successfully with {len(additional_images)} new images!')
            else:
                messages.success(request, f'Your item "{item.title}" has been updated successfully!')
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'items/edit_item.html', {'form': form, 'item': item})


@login_required
def delete_item(request, pk):
    """View to remove an item from the database"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if request.method == 'POST':
        item_title = item.title
        item.delete()
        messages.success(request, f'Your item "{item_title}" has been deleted successfully!')
        return redirect('item_list')
    return render(request, 'items/delete_item.html', {'item': item})


@login_required
def my_items(request):
    """View to display current user's items"""
    items = Item.objects.filter(user=request.user).order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'statuses': Item.STATUS_CHOICES,
    }
    return render(request, 'items/my_items.html', context)


@login_required
def mark_claimed(request, pk):
    """View to mark an item as claimed (backwards-compatibility for URLs)."""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    if request.method == 'POST':
        item.status = 'claimed'
        item.save()
        messages.success(request, f'Item "{item.title}" has been marked as claimed!')
        return redirect('item_detail', pk=item.pk)
    return render(request, 'items/mark_claimed.html', {'item': item})

@login_required
def change_item_status(request, pk):
    """View to update an item's status, with double confirmation for returning to owner."""
    item = get_object_or_404(Item, pk=pk)
    user_points, _ = UserPoints.objects.get_or_create(user=item.user)

    is_owner = request.user == item.user

    # Status-changing logic with double-confirmation for 'returned_to_owner'
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status not in dict(Item.STATUS_CHOICES):
            messages.error(request, 'Invalid status.')
            return redirect('item_detail', pk=pk)

        if new_status == 'returned_to_owner':
            confirmed_by_owner = request.POST.get('confirmed_by_owner') == 'true'
            confirmed_by_finder = request.POST.get('confirmed_by_finder') == 'true'
            if is_owner:
                # Owner is confirming receipt
                item.status = 'returned_to_owner'
                item.save()
                # Award points to finder
                finder_points, _ = UserPoints.objects.get_or_create(user=request.user)
                finder_points.points += 10  # Points to returner; you can configure amount
                finder_points.save()
                messages.success(request, f'Item "{item.title}" successfully confirmed as returned. Points awarded!')
            else:
                messages.info(request, f'Waiting for owner confirmation to finalize return.')
        else:
            item.status = new_status
            item.save()
            messages.success(request, f'Status for "{item.title}" changed to {item.get_status_display()}.')
        return redirect('item_detail', pk=item.pk)

    return render(request, 'items/change_item_status.html', {'item': item, 'is_owner': is_owner})


@login_required

def report_item(request, pk):
    """View for reporting an item as inappropriate/fraudulent."""
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason:
            Report.objects.create(item=item, reporter=request.user, reason=reason)
            messages.success(request, 'Thank you for your report. The admin team will review it.')
            return redirect('item_detail', pk=pk)
        else:
            messages.error(request, 'Please provide a reason for reporting this item.')
    return render(request, 'items/report_item.html', {'item': item, "form": CommentForm(), "comments": item.comments.filter(parent__isnull=True)})



@login_required
def add_comment(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
             Comment.objects.create(
                item=item,
                user=request.user,
                content=content
            )
            # tag_user_notification(comment)
            
    return redirect('item_detail', pk=item.pk)


def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    comments = item.comments.filter(parent__isnull=True)  # only top-level comments
    form = CommentForm()
    return render(request, "items/item_detail.html", {
        "item": item,
        "comments": comments,
        "form": form,})


@login_required
def add_reply(request, item_pk, parent_id):
    """
    Handle posting a reply to a comment.
    """
    item = get_object_or_404(Item, pk=item_pk)
    parent_comment = get_object_or_404(Comment, pk=parent_id,)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.user = request.user
            reply.item = item
            reply.parent = parent_comment  # mark this comment as a reply
            reply.save()
    
    return redirect("item_detail", pk=item.pk)



@login_required
def inbox_view(request):
    conversations = request.user.conversations.all()
    unread_count = Message.objects.filter(
        conversation__in=conversations,
        is_read=False
    ).exclude(sender=request.user).count()
    return render(request, "items/inbox.html", {
        "conversations": conversations,
        'unread_count': unread_count,})


    conversations = Conversation.objects.filter(participants=request.user)
    return render(request, "inbox.html", {"conversations": conversations})

    



@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    chat_messages = Message.objects.filter(conversation=conversation).order_by("created_at")

    if request.user not in conversation.participants.all():
        return redirect('inbox') 

    chat_messages = conversation.messages.all()
    return render(request, 'items/conversation.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
    })
    


@login_required
def send_message(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    return render(request, 'send_message.html', {'form': form, 'conversation': conversation})



@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    if other_user == request.user:
        return redirect("inbox")

    # Get the item from the request or context
    item_id = request.GET.get('item_id')
    item = get_object_or_404(Item, id=item_id)

    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).filter(item=item).first()

    if not conversation:
        conversation = Conversation.objects.create(item=item)
        conversation.participants.add(request.user, other_user)

    return redirect("conversation_detail", conversation_id=conversation.id)




# def tag_user_notification(comment):
#     usernames = re.findall(r'@(\w+)', comment.content)
    
#     for username in usernames:
#         try:
            
#             tagged_user = User.objects.get(username=username)
            
#             if tagged_user != comment.user:
#                 Notification.objects.create(
#                     user=tagged_user,
#                     message=f"You were tagged by {comment.user.username} in a comment on '{comment.item.name}'."
#                 )
#         except User.DoesNotExist:
#             continue