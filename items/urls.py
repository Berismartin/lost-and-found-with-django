from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.create_item, name='create_item'),
    path('items/<int:pk>/', views.item_detail, name='item_detail'),
    path('items/<int:pk>/add_comment/', views.add_comment, name='add_comment'),
    path('items/<int:item_pk>/add_reply/<int:parent_id>/', views.add_reply, name='add_reply'),
    path('items/<int:pk>/edit/', views.edit_item, name='edit_item'),
    path('items/<int:pk>/delete/', views.delete_item, name='delete_item'),
    path('items/<int:pk>/claim/', views.mark_claimed, name='mark_claimed'),
    path('items/<int:pk>/status/', views.change_item_status, name='change_item_status'),
    path('items/<int:pk>/report/', views.report_item, name='report_item'),
    path('my-items/', views.my_items, name='my_items'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/<int:conversation_id>/', views.start_conversation, name='start_conversation'),
    path('start_conversations/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('inbox/', views.inbox_view, name='inbox'),
    path('inbox/<int:item_id>/', views.inbox_view, name='inbox_with_item'),
    path('conversations/<int:conversation_id>/send_message/', views.send_message, name='send_message'),



    


]
