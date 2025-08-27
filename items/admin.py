from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Item Admin"""
    list_display = ('title', 'category', 'status', 'user', 'location_lost_found', 'created_at', 'is_active')
    list_filter = ('category', 'status', 'is_active', 'created_at', 'date_lost_found')
    search_fields = ('title', 'description', 'user__username', 'location_lost_found')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Item Information', {
            'fields': ('title', 'description', 'category', 'status')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Details', {
            'fields': ('user', 'location_lost_found', 'date_lost_found', 'contact_info')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
