from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.db import models
from .models import Item, ItemImage, Report, Comment, Conversation, Message
from .forms import ItemForm
from .forms import CommentForm

from users.models import UserPoints
from django.contrib.auth import get_user_model

User = get_user_model()

def home(request):
    """Home page view displaying recent items"""
    recent_items = Item.objects.filter(is_active=True).order_by('-created_at')[:6]
    return render(request, 'items/home.html', {'recent_items': recent_items})


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
    comments = item.comments.filter(parent__isnull=True)  # only top-level comments

    is_owner = request.user.is_authenticated and item.user == request.user
    context = {
        'item': item,
        'is_owner': is_owner,
    }
    return render(request, 'items/item_detail.html',{"item": item, "comments": comments})



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
    return render(request, 'items/report_item.html', {'item': item})



@login_required
def add_comment(request, pk):
    item = get_object_or_404(Item, id=pk)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                item=item,
                user=request.user,
                content=content
            )
            # tag_user_notification(comment)
            
    return redirect('item_detail', pk=item.pk)


# def item_detail(request, pk):
#     item = get_object_or_404(Item, pk=pk)
#     comments = item.comments.filter(parent__isnull=True)  # only top-level comments
#     form = CommentForm()
#     return render(request, "items/item_detail.html", {"item": item, "comments": comments})


@login_required
def add_reply(request, item_pk, parent_id):
    """
    Handle posting a reply to a comment.
    """
    item = get_object_or_404(Item, pk=item_pk)
    parent_comment = get_object_or_404(Comment, pk=parent_id)

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
            print( "Saving message:", content)  
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
        return redirect('conversation_detail', conversation_id=conversation.id)
    return redirect('inbox')

