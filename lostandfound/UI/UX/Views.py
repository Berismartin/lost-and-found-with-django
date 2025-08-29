from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification # Assumes this model exists

@login_required
def get_notifications(request):
    """
    An API endpoint to fetch notifications for the current user.
    """
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-timestamp')
    
    data = [{
        'id': notification.id,
        'message': notification.message,
        'timestamp': notification.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'url': notification.url, # Assuming a URL field for a link
    } for notification in notifications]
    
    # Optionally, you can mark them as read after fetching
    notifications.update(is_read=True)
    
    return JsonResponse({'notifications': data, 'count': len(data)})