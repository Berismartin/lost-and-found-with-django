from django.shortcuts import render
from django.db.models import Q, Count, Avg
from items.models import Item, Category
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Notification
import json
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View



class SearchView(View):
    """
    Handle search queries and filters for items with advanced filtering options.
    """
    template_name = 'search_results.html'
    paginate_by = 20
    
    def get(self, request):
        """
        Handle GET requests for search with filters
        """
        # Get search parameters
        query = request.GET.get('q', '').strip()
        category_id = request.GET.get('category', '')
        date_filter = request.GET.get('date_filter', '')
        price_min = request.GET.get('price_min', '')
        price_max = request.GET.get('price_max', '')
        sort_by = request.GET.get('sort', '-created_at')
        page = request.GET.get('page', 1)
        per_page = min(int(request.GET.get('per_page', self.paginate_by)), 100)
        
        # Additional filters
        status = request.GET.get('status', '')
        location = request.GET.get('location', '')
        condition = request.GET.get('condition', '')
        featured_only = request.GET.get('featured', '') == 'true'
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Start with base queryset
        items = Item.objects.select_related('category', 'user').prefetch_related('images')
        
        # Apply search query
        if query:
            items = self._apply_search_query(items, query)
        
        # Apply filters
        items = self._apply_filters(items, {
            'category_id': category_id,
            'date_filter': date_filter,
            'price_min': price_min,
            'price_max': price_max,
            'status': status,
            'location': location,
            'condition': condition,
            'featured_only': featured_only
        })
        
        # Apply sorting
        items = self._apply_sorting(items, sort_by)
        
        # Get filter options for the template
        filter_options = self._get_filter_options()
        
        # Paginate results
        paginator = Paginator(items, per_page)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Prepare context
        context = {
            'items': page_obj,
            'query': query,
            'current_filters': {
                'category': category_id,
                'date_filter': date_filter,
                'price_min': price_min,
                'price_max': price_max,
                'sort': sort_by,
                'status': status,
                'location': location,
                'condition': condition,
                'featured': featured_only
            },
            'filter_options': filter_options,
            'total_results': paginator.count,
            'search_stats': self._get_search_stats(items.model.objects.all(), query),
            'suggested_searches': self._get_suggested_searches(query) if query else [],
        }
        
        # Return JSON for AJAX requests
        if is_ajax:
            return self._ajax_response(page_obj, context)
        
        return render(request, self.template_name, context)
    
    def _apply_search_query(self, queryset, query):
        """
        Apply search query to the queryset with weighted relevance
        """
        if not query:
            return queryset
        
        # Split query into terms
        terms = query.split()
        
        # Build search conditions
        search_conditions = Q()
        
        for term in terms:
            term_conditions = (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(tags__icontains=term) |
                Q(category__name__icontains=term) |
                Q(location__icontains=term)
            )
            search_conditions &= term_conditions
        
        # Apply search with relevance scoring (simplified)
        return queryset.filter(search_conditions).distinct()
    
    def _apply_filters(self, queryset, filters):
        """
        Apply various filters to the queryset
        """
        # Category filter
        if filters['category_id']:
            try:
                category_id = int(filters['category_id'])
                queryset = queryset.filter(category_id=category_id)
            except ValueError:
                pass
        
        # Date filter
        if filters['date_filter']:
            now = timezone.now()
            if filters['date_filter'] == 'today':
                queryset = queryset.filter(created_at__date=now.date())
            elif filters['date_filter'] == 'week':
                week_ago = now - timedelta(days=7)
                queryset = queryset.filter(created_at__gte=week_ago)
            elif filters['date_filter'] == 'month':
                month_ago = now - timedelta(days=30)
                queryset = queryset.filter(created_at__gte=month_ago)
            elif filters['date_filter'] == 'year':
                year_ago = now - timedelta(days=365)
                queryset = queryset.filter(created_at__gte=year_ago)
        
        # Price range filter
        if filters['price_min']:
            try:
                price_min = float(filters['price_min'])
                queryset = queryset.filter(price__gte=price_min)
            except ValueError:
                pass
        
        if filters['price_max']:
            try:
                price_max = float(filters['price_max'])
                queryset = queryset.filter(price__lte=price_max)
            except ValueError:
                pass
        
        # Status filter
        if filters['status']:
            queryset = queryset.filter(status=filters['status'])
        
        # Location filter
        if filters['location']:
            queryset = queryset.filter(location__icontains=filters['location'])
        
        # Condition filter
        if filters['condition']:
            queryset = queryset.filter(condition=filters['condition'])
        
        # Featured only filter
        if filters['featured_only']:
            queryset = queryset.filter(is_featured=True)
        
        return queryset
    
    def _apply_sorting(self, queryset, sort_by):
        """
        Apply sorting to the queryset
        """
        valid_sort_options = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_low': 'price',
            'price_high': '-price',
            'title_az': 'title',
            'title_za': '-title',
            'popular': '-view_count',
            'rating': '-average_rating',
            'featured': '-is_featured',
            '-created_at': '-created_at',  # Default fallback
        }
        
        sort_field = valid_sort_options.get(sort_by, '-created_at')
        return queryset.order_by(sort_field)
    
    def _get_filter_options(self):
        """
        Get available filter options for the template
        """
        return {
            'categories': Category.objects.annotate(
                item_count=Count('items')
            ).filter(item_count__gt=0).order_by('name'),
            'date_ranges': [
                ('', 'Any time'),
                ('today', 'Today'),
                ('week', 'This week'),
                ('month', 'This month'),
                ('year', 'This year'),
            ],
            'sort_options': [
                ('-created_at', 'Newest first'),
                ('created_at', 'Oldest first'),
                ('price', 'Price: Low to high'),
                ('-price', 'Price: High to low'),
                ('title', 'Title: A-Z'),
                ('-title', 'Title: Z-A'),
                ('-view_count', 'Most popular'),
                ('-average_rating', 'Highest rated'),
            ],
            'status_options': [
                ('', 'All status'),
                ('active', 'Active'),
                ('sold', 'Sold'),
                ('pending', 'Pending'),
                ('draft', 'Draft'),
            ],
            'condition_options': [
                ('', 'Any condition'),
                ('new', 'New'),
                ('like_new', 'Like New'),
                ('good', 'Good'),
                ('fair', 'Fair'),
                ('poor', 'Poor'),
            ]
        }
    
    def _get_search_stats(self, all_items, query):
        """
        Get statistics about search results
        """
        if not query:
            return {}
        
        total_items = all_items.count()
        
        # Get price statistics
        price_stats = all_items.aggregate(
            min_price=models.Min('price'),
            max_price=models.Max('price'),
            avg_price=Avg('price')
        )
        
        return {
            'total_items': total_items,
            'price_range': {
                'min': price_stats['min_price'] or 0,
                'max': price_stats['max_price'] or 0,
                'avg': price_stats['avg_price'] or 0,
            }
        }
    
    def _get_suggested_searches(self, query):
        """
        Generate suggested search terms based on current query
        """
        if not query or len(query) < 3:
            return []
        
        # Get similar items based on title similarity
        similar_items = Item.objects.filter(
            Q(title__icontains=query) | Q(category__name__icontains=query)
        ).values_list('title', flat=True)[:5]
        
        # Extract unique words for suggestions
        suggestions = set()
        for title in similar_items:
            words = title.lower().split()
            for word in words:
                if len(word) > 3 and word not in query.lower():
                    suggestions.add(word.capitalize())
        
        return list(suggestions)[:5]
    
    def _ajax_response(self, page_obj, context):
        """
        Return JSON response for AJAX requests
        """
        items_data = []
        for item in page_obj:
            items_data.append({
                'id': item.id,
                'title': item.title,
                'description': item.description[:150] + '...' if len(item.description) > 150 else item.description,
                'price': float(item.price),
                'currency': getattr(item, 'currency', 'USD'),
                'category': item.category.name if item.category else '',
                'location': item.location,
                'condition': item.get_condition_display() if hasattr(item, 'get_condition_display') else item.condition,
                'status': item.status,
                'is_featured': getattr(item, 'is_featured', False),
                'image_url': item.get_primary_image_url() if hasattr(item, 'get_primary_image_url') else '',
                'url': item.get_absolute_url() if hasattr(item, 'get_absolute_url') else f'/items/{item.id}/',
                'created_at': item.created_at.isoformat(),
                'view_count': getattr(item, 'view_count', 0),
                'user': {
                    'username': item.user.username,
                    'display_name': item.user.get_full_name() or item.user.username,
                } if item.user else None
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': page_obj.paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_results': page_obj.paginator.count,
                'per_page': page_obj.paginator.per_page,
                'start_index': page_obj.start_index(),
                'end_index': page_obj.end_index(),
            },
            'query': context['query'],
            'filters': context['current_filters'],
            'stats': context['search_stats'],
            'suggestions': context['suggested_searches'],
        })

        return JsonResponse({'success': False, 'error': 'Invalid request'}) 

@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    API endpoint to fetch the latest notifications for a user using AJAX.
    
    Query Parameters:
    - page: Page number for pagination (default: 1)
    - limit: Number of notifications per page (default: 20, max: 100)
    - unread_only: Filter for unread notifications only (default: false)
    - mark_as_read: Mark fetched notifications as read (default: false)
    """
    try:
        user = request.user
        
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 100)  # Cap at 100
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'
        mark_as_read = request.GET.get('mark_as_read', 'false').lower() == 'true'
        
        # Build queryset
        notifications = Notification.objects.filter(user=user).order_by('-created_at')
        
        # Filter for unread only if requested
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        # Get total counts for response metadata
        total_count = notifications.count()
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        
        # Paginate results
        paginator = Paginator(notifications, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize notifications
        notifications_data = []
        notification_ids = []
        
        for notification in page_obj.object_list:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
                'icon': notification.get_icon(),  # Assuming a method that returns icon class/name
                'priority': notification.priority if hasattr(notification, 'priority') else 'normal'
            })
            
            if not notification.is_read:
                notification_ids.append(notification.id)
        
        # Mark notifications as read if requested
        if mark_as_read and notification_ids:
            Notification.objects.filter(
                id__in=notification_ids,
                user=user
            ).update(is_read=True, read_at=timezone.now())
            
            # Update unread count after marking as read
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
        
        # Prepare response
        response_data = {
            'success': True,
            'notifications': notifications_data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': page_obj.paginator.num_pages,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'total_count': total_count,
                'per_page': limit
            },
            'metadata': {
                'unread_count': unread_count,
                'total_count': total_count,
                'fetched_count': len(notifications_data)
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
    
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid parameter value',
            'message': str(e)
        }, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Internal server error',
            'message': 'An error occurred while fetching notifications'
        }, status=500)

