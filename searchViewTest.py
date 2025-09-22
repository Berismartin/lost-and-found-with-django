# tests/test_search_view.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
from unittest.mock import patch

from myapp.models import Item, Category  # Adjust import path as needed
from myapp.views import SearchView


class SearchViewRegressionTests(TestCase):
    """
    Comprehensive regression tests for SearchView functionality
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create test categories
        self.electronics_cat = Category.objects.create(name='Electronics')
        self.books_cat = Category.objects.create(name='Books')
        self.furniture_cat = Category.objects.create(name='Furniture')
        
        # Create test items with varied data
        self.items_data = [
            {
                'title': 'iPhone 13 Pro Max',
                'description': 'Brand new iPhone 13 Pro Max 128GB',
                'price': Decimal('999.99'),
                'category': self.electronics_cat,
                'location': 'New York',
                'condition': 'new',
                'status': 'active',
                'is_featured': True,
                'tags': 'smartphone,apple,ios',
                'view_count': 150,
                'average_rating': 4.8
            },
            {
                'title': 'Samsung Galaxy S21',
                'description': 'Used Samsung Galaxy S21 in good condition',
                'price': Decimal('450.00'),
                'category': self.electronics_cat,
                'location': 'Los Angeles',
                'condition': 'good',
                'status': 'active',
                'is_featured': False,
                'tags': 'smartphone,android,samsung',
                'view_count': 75,
                'average_rating': 4.2
            },
            {
                'title': 'Python Programming Book',
                'description': 'Learn Python programming with this comprehensive guide',
                'price': Decimal('29.99'),
                'category': self.books_cat,
                'location': 'Chicago',
                'condition': 'like_new',
                'status': 'active',
                'is_featured': False,
                'tags': 'programming,python,education',
                'view_count': 25,
                'average_rating': 4.5
            },
            {
                'title': 'Office Chair',
                'description': 'Ergonomic office chair, barely used',
                'price': Decimal('125.00'),
                'category': self.furniture_cat,
                'location': 'Miami',
                'condition': 'like_new',
                'status': 'sold',
                'is_featured': False,
                'tags': 'furniture,office,ergonomic',
                'view_count': 40,
                'average_rating': 4.0
            },
            {
                'title': 'MacBook Pro 2021',
                'description': 'MacBook Pro M1 chip, excellent condition',
                'price': Decimal('1299.99'),
                'category': self.electronics_cat,
                'location': 'Seattle',
                'condition': 'like_new',
                'status': 'pending',
                'is_featured': True,
                'tags': 'laptop,apple,macbook',
                'view_count': 200,
                'average_rating': 4.9
            }
        ]
        
        self.items = []
        for i, item_data in enumerate(self.items_data):
            # Create items with different creation dates
            created_at = timezone.now() - timedelta(days=i)
            item = Item.objects.create(
                user=self.user,
                created_at=created_at,
                **item_data
            )
            self.items.append(item)
        
        self.search_url = reverse('search')  # Adjust URL name as needed

    def test_basic_search_query(self):
        """Test basic search functionality with query parameter"""
        response = self.client.get(self.search_url, {'q': 'iPhone'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13 Pro Max')
        self.assertNotContains(response, 'Samsung Galaxy')
        
        # Check context variables
        self.assertIn('items', response.context)
        self.assertIn('query', response.context)
        self.assertEqual(response.context['query'], 'iPhone')
        self.assertTrue(response.context['total_results'] >= 1)

    def test_empty_search_query(self):
        """Test search with empty query returns all items"""
        response = self.client.get(self.search_url, {'q': ''})
        
        self.assertEqual(response.status_code, 200)
        # Should return all active items (3 out of 5, excluding sold/pending)
        active_items = Item.objects.filter(status='active').count()
        self.assertEqual(response.context['total_results'], active_items)

    def test_no_search_results(self):
        """Test search with query that returns no results"""
        response = self.client.get(self.search_url, {'q': 'nonexistentitem123'})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_results'], 0)
        self.assertEqual(len(response.context['items']), 0)

    def test_multi_term_search(self):
        """Test search with multiple terms (AND logic)"""
        response = self.client.get(self.search_url, {'q': 'Samsung Galaxy'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Samsung Galaxy S21')
        self.assertNotContains(response, 'iPhone')

    def test_category_filter(self):
        """Test filtering by category"""
        response = self.client.get(self.search_url, {
            'category': str(self.electronics_cat.id)
        })
        
        self.assertEqual(response.status_code, 200)
        electronics_items = Item.objects.filter(category=self.electronics_cat).count()
        
        # Verify all returned items are electronics
        for item in response.context['items']:
            self.assertEqual(item.category, self.electronics_cat)

    def test_invalid_category_filter(self):
        """Test category filter with invalid ID"""
        response = self.client.get(self.search_url, {'category': 'invalid'})
        
        self.assertEqual(response.status_code, 200)
        # Should not crash, should ignore invalid category

    def test_price_range_filter(self):
        """Test price range filtering"""
        response = self.client.get(self.search_url, {
            'price_min': '100',
            'price_max': '500'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all returned items are within price range
        for item in response.context['items']:
            self.assertGreaterEqual(item.price, Decimal('100'))
            self.assertLessEqual(item.price, Decimal('500'))

    def test_price_filter_with_invalid_values(self):
        """Test price filtering with invalid values"""
        response = self.client.get(self.search_url, {
            'price_min': 'invalid',
            'price_max': 'also_invalid'
        })
        
        self.assertEqual(response.status_code, 200)
        # Should not crash, should ignore invalid prices

    def test_date_filter_today(self):
        """Test date filtering for today"""
        # Create an item today
        today_item = Item.objects.create(
            title='Today Item',
            description='Created today',
            price=Decimal('50.00'),
            category=self.books_cat,
            user=self.user,
            status='active',
            created_at=timezone.now()
        )
        
        response = self.client.get(self.search_url, {'date_filter': 'today'})
        
        self.assertEqual(response.status_code, 200)
        # Should only return today's item
        self.assertContains(response, 'Today Item')

    def test_date_filter_week(self):
        """Test date filtering for this week"""
        response = self.client.get(self.search_url, {'date_filter': 'week'})
        
        self.assertEqual(response.status_code, 200)
        # Should return items from the last 7 days

    def test_status_filter(self):
        """Test filtering by status"""
        response = self.client.get(self.search_url, {'status': 'sold'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all returned items have 'sold' status
        for item in response.context['items']:
            self.assertEqual(item.status, 'sold')

    def test_location_filter(self):
        """Test location filtering"""
        response = self.client.get(self.search_url, {'location': 'New York'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'iPhone 13 Pro Max')

    def test_condition_filter(self):
        """Test condition filtering"""
        response = self.client.get(self.search_url, {'condition': 'new'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all returned items have 'new' condition
        for item in response.context['items']:
            self.assertEqual(item.condition, 'new')

    def test_featured_only_filter(self):
        """Test featured only filter"""
        response = self.client.get(self.search_url, {'featured': 'true'})
        
        self.assertEqual(response.status_code, 200)
        
        # Verify all returned items are featured
        for item in response.context['items']:
            self.assertTrue(item.is_featured)

    def test_sorting_options(self):
        """Test different sorting options"""
        sort_tests = [
            ('newest', '-created_at'),
            ('oldest', 'created_at'),
            ('price_low', 'price'),
            ('price_high', '-price'),
            ('title_az', 'title'),
            ('title_za', '-title'),
            ('popular', '-view_count'),
        ]
        
        for sort_param, expected_order in sort_tests:
            with self.subTest(sort=sort_param):
                response = self.client.get(self.search_url, {'sort': sort_param})
                self.assertEqual(response.status_code, 200)
                # Verify items are returned (basic check)
                self.assertIn('items', response.context)

    def test_pagination(self):
        """Test pagination functionality"""
        # Test with custom per_page
        response = self.client.get(self.search_url, {
            'per_page': '2',
            'page': '1'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.context['items']), 2)
        
        # Test page 2
        response = self.client.get(self.search_url, {
            'per_page': '2',
            'page': '2'
        })
        
        self.assertEqual(response.status_code, 200)

    def test_pagination_invalid_page(self):
        """Test pagination with invalid page numbers"""
        # Test non-integer page
        response = self.client.get(self.search_url, {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)
        
        # Test page beyond range
        response = self.client.get(self.search_url, {'page': '999'})
        self.assertEqual(response.status_code, 200)

    def test_per_page_limit(self):
        """Test per_page parameter limits"""
        response = self.client.get(self.search_url, {'per_page': '200'})
        
        self.assertEqual(response.status_code, 200)
        # Should be limited to 100 max
        self.assertLessEqual(len(response.context['items']), 100)

    def test_combined_filters(self):
        """Test multiple filters applied together"""
        response = self.client.get(self.search_url, {
            'q': 'phone',
            'category': str(self.electronics_cat.id),
            'price_min': '400',
            'condition': 'good',
            'sort': 'price_low'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Verify filters are applied
        context = response.context
        self.assertEqual(context['current_filters']['category'], str(self.electronics_cat.id))
        self.assertEqual(context['current_filters']['price_min'], '400')
        self.assertEqual(context['current_filters']['condition'], 'good')

    def test_ajax_request(self):
        """Test AJAX request returns JSON response"""
        response = self.client.get(
            self.search_url,
            {'q': 'iPhone'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('items', data)
        self.assertIn('pagination', data)
        self.assertIn('query', data)
        self.assertIn('filters', data)

    def test_ajax_response_structure(self):
        """Test AJAX response has correct structure"""
        response = self.client.get(
            self.search_url,
            {'q': 'iPhone'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        
        # Verify main structure
        required_keys = ['success', 'items', 'pagination', 'query', 'filters', 'stats', 'suggestions']
        for key in required_keys:
            self.assertIn(key, data)
        
        # Verify item structure
        if data['items']:
            item = data['items'][0]
            item_keys = ['id', 'title', 'description', 'price', 'category', 'location', 'condition', 'status', 'url', 'created_at']
            for key in item_keys:
                self.assertIn(key, item)
        
        # Verify pagination structure
        pagination = data['pagination']
        pagination_keys = ['current_page', 'total_pages', 'has_next', 'has_previous', 'total_results', 'per_page']
        for key in pagination_keys:
            self.assertIn(key, pagination)

    def test_search_stats(self):
        """Test search statistics are calculated correctly"""
        response = self.client.get(self.search_url, {'q': 'phone'})
        
        self.assertEqual(response.status_code, 200)
        stats = response.context['search_stats']
        
        self.assertIn('total_items', stats)
        self.assertIn('price_range', stats)
        self.assertIn('min', stats['price_range'])
        self.assertIn('max', stats['price_range'])
        self.assertIn('avg', stats['price_range'])

    def test_suggested_searches(self):
        """Test suggested searches are generated"""
        response = self.client.get(self.search_url, {'q': 'iphone'})
        
        self.assertEqual(response.status_code, 200)
        suggestions = response.context['suggested_searches']
        
        self.assertIsInstance(suggestions, list)
        # Should have at most 5 suggestions
        self.assertLessEqual(len(suggestions), 5)

    def test_filter_options_structure(self):
        """Test filter options are provided correctly"""
        response = self.client.get(self.search_url)
        
        self.assertEqual(response.status_code, 200)
        filter_options = response.context['filter_options']
        
        required_options = ['categories', 'date_ranges', 'sort_options', 'status_options', 'condition_options']
        for option in required_options:
            self.assertIn(option, filter_options)
        
        # Verify categories have item counts
        for category in filter_options['categories']:
            self.assertTrue(hasattr(category, 'item_count'))

    def test_search_query_edge_cases(self):
        """Test edge cases for search queries"""
        edge_cases = [
            '',  # Empty string
            '   ',  # Whitespace only
            'a',  # Single character
            'a' * 200,  # Very long query
            'special!@#$%^&*()characters',  # Special characters
            'search\nwith\nnewlines',  # Newlines
        ]
        
        for query in edge_cases:
            with self.subTest(query=repr(query)):
                response = self.client.get(self.search_url, {'q': query})
                self.assertEqual(response.status_code, 200)

    def test_performance_with_many_results(self):
        """Test search performance doesn't degrade with many results"""
        # This test would be more meaningful with a larger dataset
        # For now, just ensure it doesn't crash with current data
        
        response = self.client.get(self.search_url, {'per_page': '100'})
        self.assertEqual(response.status_code, 200)

    def test_search_across_related_fields(self):
        """Test search includes related model fields (category, user)"""
        response = self.client.get(self.search_url, {'q': 'Electronics'})
        
        self.assertEqual(response.status_code, 200)
        # Should find items in electronics category
        self.assertTrue(response.context['total_results'] > 0)

    def test_search_tags_field(self):
        """Test search includes tags field"""
        response = self.client.get(self.search_url, {'q': 'smartphone'})
        
        self.assertEqual(response.status_code, 200)
        # Should find items with smartphone tag
        self.assertTrue(response.context['total_results'] > 0)

    def test_context_variables_present(self):
        """Test all required context variables are present"""
        response = self.client.get(self.search_url, {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        
        required_context = [
            'items', 'query', 'current_filters', 'filter_options',
            'total_results', 'search_stats', 'suggested_searches'
        ]
        
        for var in required_context:
            self.assertIn(var, response.context, f"Missing context variable: {var}")

    def test_current_filters_in_context(self):
        """Test current filters are preserved in context"""
        filters = {
            'q': 'test query',
            'category': str(self.electronics_cat.id),
            'price_min': '100',
            'price_max': '500',
            'sort': 'price_low',
            'status': 'active',
            'location': 'New York',
            'condition': 'new',
            'featured': 'true'
        }
        
        response = self.client.get(self.search_url, filters)
        
        self.assertEqual(response.status_code, 200)
        current_filters = response.context['current_filters']
        
        # Check all filters are preserved
        self.assertEqual(current_filters['category'], filters['category'])
        self.assertEqual(current_filters['price_min'], filters['price_min'])
        self.assertEqual(current_filters['price_max'], filters['price_max'])
        self.assertEqual(current_filters['sort'], filters['sort'])
        self.assertEqual(current_filters['status'], filters['status'])
        self.assertEqual(current_filters['location'], filters['location'])
        self.assertEqual(current_filters['condition'], filters['condition'])
        self.assertTrue(current_filters['featured'])

    def tearDown(self):
        """Clean up after tests"""
        # Clean up is handled automatically by Django test framework
        # But you can add custom cleanup here if needed
        pass


class SearchViewUnitTests(TestCase):
    """
    Unit tests for individual SearchView methods
    """
    
    def setUp(self):
        self.view = SearchView()
        self.user = User.objects.create_user(username='testuser')
        self.category = Category.objects.create(name='Test Category')
        
        self.item = Item.objects.create(
            title='Test Item',
            description='Test description',
            price=Decimal('99.99'),
            category=self.category,
            user=self.user,
            location='Test Location',
            condition='new',
            status='active'
        )

    def test_apply_search_query_method(self):
        """Test _apply_search_query method directly"""
        queryset = Item.objects.all()
        
        # Test with query
        result = self.view._apply_search_query(queryset, 'Test')
        self.assertTrue(result.filter(title__icontains='Test').exists())
        
        # Test with empty query
        result = self.view._apply_search_query(queryset, '')
        self.assertEqual(list(result), list(queryset))

    def test_apply_filters_method(self):
        """Test _apply_filters method directly"""
        queryset = Item.objects.all()
        
        filters = {
            'category_id': str(self.category.id),
            'price_min': '50',
            'price_max': '150',
            'status': 'active',
            'location': '',
            'condition': 'new',
            'featured_only': False,
            'date_filter': ''
        }
        
        result = self.view._apply_filters(queryset, filters)
        
        # Should return our test item
        self.assertIn(self.item, result)

    def test_apply_sorting_method(self):
        """Test _apply_sorting method directly"""
        queryset = Item.objects.all()
        
        # Test valid sort option
        result = self.view._apply_sorting(queryset, 'newest')
        self.assertEqual(result.query.order_by, ('-created_at',))
        
        # Test invalid sort option (should default)
        result = self.view._apply_sorting(queryset, 'invalid_sort')
        self.assertEqual(result.query.order_by, ('-created_at',))

    def test_get_filter_options_method(self):
        """Test _get_filter_options method directly"""
        options = self.view._get_filter_options()
        
        required_keys = ['categories', 'date_ranges', 'sort_options', 'status_options', 'condition_options']
        for key in required_keys:
            self.assertIn(key, options)
        
        # Verify structure
        self.assertIsInstance(options['categories'], type(Category.objects.none()))
        self.assertIsInstance(options['date_ranges'], list)
        self.assertIsInstance(options['sort_options'], list)

    def test_get_search_stats_method(self):
        """Test _get_search_stats method directly"""
        queryset = Item.objects.all()
        
        stats = self.view._get_search_stats(queryset, 'test query')
        
        self.assertIn('total_items', stats)
        self.assertIn('price_range', stats)
        
        # Test with empty query
        stats_empty = self.view._get_search_stats(queryset, '')
        self.assertEqual(stats_empty, {})

    def test_get_suggested_searches_method(self):
        """Test _get_suggested_searches method directly"""
        # Test with valid query
        suggestions = self.view._get_suggested_searches('Test')
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 5)
        
        # Test with short query
        suggestions_short = self.view._get_suggested_searches('Te')
        self.assertEqual(suggestions_short, [])
        
        # Test with empty query
        suggestions_empty = self.view._get_suggested_searches('')
        self.assertEqual(suggestions_empty, [])