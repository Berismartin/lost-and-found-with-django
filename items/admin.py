from django.contrib import admin
from .models import Item, ItemImage, Report

class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1
    fields = ('image', 'caption', 'order')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'user', 'location_lost_found', 'created_at', 'is_active')
    list_filter = ('category', 'status', 'is_active', 'created_at', 'date_lost_found')
    search_fields = ('title', 'description', 'user__username', 'location_lost_found')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Item Information', {'fields': ('title', 'description', 'category', 'status')}),
        ('Media', {'fields': ('image',)}),
        ('Details', {'fields': ('user', 'location_lost_found', 'date_lost_found', 'contact_info')}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [ItemImageInline]
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ('item', 'image', 'caption', 'order', 'created_at')
    list_filter = ('created_at', 'item__category', 'item__status')
    search_fields = ('item__title', 'caption')
    list_editable = ('order', 'caption')
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'item__user')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('item', 'reporter', 'reason', 'created_at', 'resolved')
    list_filter = ('created_at', 'resolved', 'item__status')
    search_fields = ('item__title', 'reporter__username', 'reason')
    readonly_fields = ('created_at',)
    actions = ['mark_resolved']
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)
    mark_resolved.short_description = 'Mark selected reports as resolved'
