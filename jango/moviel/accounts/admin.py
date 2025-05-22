from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    # Add the new fields to the form
    add_form = UserCreationForm
    form = UserChangeForm
    model = CustomUser

    # Customize the list view
    list_display = ('username', 'email', 'role', 'is_active', 'phone_number', 'license_number')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number', 'license_number')
    ordering = ('username',)

    # Customize the detail view with fieldsets
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (_('Role & License'), {
            'fields': ('role', 'license_number'),
            'description': 'License number is required for foster homes.'
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Customize the add view with specific fields
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone_number', 'license_number'),
        }),
    )

    # Read-only fields
    readonly_fields = ('date_joined', 'last_login')

    # Actions
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        queryset.update(is_active=True)
    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_users.short_description = "Deactivate selected users"

    # Save model override to handle the automatic role assignment for superusers
    def save_model(self, request, obj, form, change):
        if obj.is_superuser:
            obj.role = 'admin'
        super().save_model(request, obj, form, change)

    # Custom get_queryset to optimize database queries
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

admin.site.register(CustomUser, CustomUserAdmin)