from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.db import models
from .models import Item, ItemImage
from .forms import ItemForm


def home(request):
    """Home page view displaying recent items"""
    recent_items = Item.objects.filter(is_active=True).order_by('-created_at')[:6]
    return render(request, 'items/home.html', {'recent_items': recent_items})


def item_list(request):
    """View to display all active items with filtering and pagination"""
    items = Item.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        items = items.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location_lost_found__icontains=search_query)
        )
    
    # Category filtering
    category_filter = request.GET.get('category')
    if category_filter:
        items = items.filter(category=category_filter)
    
    # Status filtering
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(items, 9)  # Show 9 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get choices for filter dropdowns
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
            
            # Handle multiple additional images
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
    
    # Check if the current user is the owner of the item
    is_owner = request.user.is_authenticated and item.user == request.user
    
    context = {
        'item': item,
        'is_owner': is_owner,
    }
    
    return render(request, 'items/item_detail.html', context)


@login_required
def edit_item(request, pk):
    """View to handle the form for updating an existing item"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            
            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            if additional_images:
                # Get the current highest order number
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
    
    # Status filtering for user's own items
    status_filter = request.GET.get('status')
    if status_filter:
        items = items.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(items, 10)  # Show 10 items per page
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
    """View to mark an item as claimed"""
    item = get_object_or_404(Item, pk=pk, user=request.user)
    
    if request.method == 'POST':
        item.status = 'claimed'
        item.save()
        messages.success(request, f'Item "{item.title}" has been marked as claimed!')
        return redirect('item_detail', pk=item.pk)
    
    return render(request, 'items/mark_claimed.html', {'item': item})
