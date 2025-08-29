from django.shortcuts import render
from django.db.models import Q
from .models import Item

def search_view(request):
    """
    Handles search queries and filters for lost and found items.
    """
    queryset = Item.objects.all()
    query = request.GET.get('q')
    category_filter = request.GET.get('category')
    date_filter = request.GET.get('date_posted')
    
    # 1. Keyword Search
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    # 2. Category Filter
    if category_filter:
        queryset = queryset.filter(category=category_filter)
        
    # 3. Date Filter (e.g., filtering by a specific date)
    if date_filter:
        # Assuming date_filter is in 'YYYY-MM-DD' format
        queryset = queryset.filter(date_posted__date=date_filter)

    # You could add more filters here (e.g., location)
    
    context = {
        'items': queryset,
        'query': query,
        'categories': Item.CATEGORIES, # Assuming you have this defined in your model
        'selected_category': category_filter,
    }
    
    return render(request, 'search_results.html', context)