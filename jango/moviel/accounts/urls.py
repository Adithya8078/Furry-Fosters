from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('accounts/login/', views.login_view, name='login'),
    path('logout', views.Logout, name='logout'),
    
    path('admin/approve-foster/<int:user_id>/', views.approve_foster_view, name='approve_foster_view'),
    path('custom_password_reset/', views.custom_password_reset, name='custom_password_reset'),
    path('custom_password_reset_confirm/<uidb64>/<token>/', views.custom_password_reset_confirm, name='custom_password_reset_confirm'),
    

]
