from django.contrib import admin
from .models import Payment, Pet, Request, Cart, Message

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'amount', 'upi_id', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'upi_id')
    date_hierarchy = 'created_at'

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'breed', 'age', 'price', 'gender', 'health_status', 'availability', 'location')
    list_filter = ('category', 'availability', 'gender', 'health_status')
    search_fields = ('name', 'breed', 'location')
    list_editable = ('availability', 'health_status', 'price')
    readonly_fields = ('foster_home',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'breed', 'age', 'gender')
        }),
        ('Health & Status', {
            'fields': ('health_status', 'availability', 'vaccine_report')
        }),
        ('Additional Details', {
            'fields': ('price', 'about', 'location', 'image', 'foster_home')
        }),
    )

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'pet', 'status', 'request_date', 'payment')
    list_filter = ('status', 'request_date')
    search_fields = ('user__username', 'pet__name')
    raw_id_fields = ('user', 'pet', 'payment')
    readonly_fields = ('request_date',)
    fieldsets = (
        ('Request Information', {
            'fields': ('user', 'pet', 'status', 'payment')
        }),
        ('Adopter Details', {
            'fields': ('intent', 'experience', 'home_environment')
        }),
    )

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username',)
    filter_horizontal = ('requests',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'pet', 'created_at', 'read')
    list_filter = ('read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'pet__name', 'content')
    raw_id_fields = ('sender', 'recipient', 'pet')
    readonly_fields = ('created_at',)