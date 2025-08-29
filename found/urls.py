from django.urls import path
from . import views

urlpatterns = [
    # path('', views.boy, name='boy'),
    path('', views.home, name='home'),  
    path('inbox/', views.inbox_view, name='inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/<int:conversation_id>/send_message/', views.send_message, name='send_message'),
    # path('found/', views.boy, name='boy'),
    # path('send_message/',views.send_message, name='send_message'),

    path('item/<int:item_id>/add_comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/reply/', views.add_reply, name='add_reply'),
]    