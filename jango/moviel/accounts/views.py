from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate,logout
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser
from django.utils.encoding import force_str
from .forms import CustomUserCreationForm,CustomPasswordResetForm,CustomSetPasswordForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
@user_passes_test(lambda u: u.is_superuser)  
# Restrict to superusers


def approve_foster_view(request, user_id):
    """Approve or reject foster registration."""
    try:
        user = CustomUser.objects.get(id=user_id, role='foster', is_active=False)
    except CustomUser.DoesNotExist:
        return render(request, 'error_page.html', {'message': 'User not found or already active.'})

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            user.is_active = True
            user.is_approved = True
            user.save()

            # Send approval email
            send_mail(
                'Foster Registration Approved',
                f'Hello {user.username},\n\nYour foster registration has been approved. You can now log in to your account.',
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )

        elif action == 'reject':
            user.delete()

        return redirect('admin_page', user_id=request.user.id)

    return render(request, 'admin/approve_foster.html', {'user': user})




def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user instance but delay database commit
            user = form.save(commit=False)

            # Check if the username already exists
            if CustomUser.objects.filter(username=user.username).exists():
                form.add_error('username', 'The username is already taken.')
                return render(request, 'registration/register.html', {'form': form})

            # Check if the phone number already exists
            if CustomUser.objects.filter(phone_number=user.phone_number).exists():
                form.add_error('phone_number', 'The phone number is already registered.')
                return render(request, 'registration/register.html', {'form': form})

            if user.role == 'foster':
                # Set the foster user as inactive by default
                user.is_active = False
                user.save()

                # Send email to admin about new foster registration
                

                # Notify the foster user about the approval process
                send_mail(
                    'Foster Registration Pending Approval',
                    'Thank you for registering as a foster. You will be able to log in after your account is approved.',
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                
                return render(request, 'registration/pending_approval.html', {'user': user})

            else:
                # For non-foster roles, activate and log in the user
                user.is_active = True
                user.save()
                login(request, user)

                # Send a thank-you email to the user
                send_mail(
                    'Thanks for Registering',
                    'Thank you for registering with us. You can now log in and start using the platform.',
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )

                
                return redirect('house')  # Redirect to the home page

        # If form is invalid, render the page with error messages
        

    else:
        form = CustomUserCreationForm()
        # Exclude 'admin' from the role choices
        form.fields['role'].choices = [
            choice for choice in form.fields['role'].choices if choice[0] != 'admin'
        ]

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user:
                if user.role == 'foster' and not user.is_active:
                    messages.error(request, "Your foster account is pending approval.")
                    return render(request, 'registration/not_approved.html')

                login(request, user)

                # Role-based redirects
                if user.is_superuser:
                    return redirect('admin_page', user_id=user.id)
                elif user.role == 'adopter':
                    return redirect('house')
                elif user.role == 'foster':
                    return redirect('foster_page', user_id=user.id)
                else:
                    return redirect('house')
        else:
            # Add a more user-friendly error message
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


def Logout(request):
    """Log out the user."""
    auth.logout(request)
    return redirect('/home')

def custom_password_reset(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                # Generate reset link
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = request.build_absolute_uri(
                    reverse('custom_password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )

                # Send email
                send_mail(
                    subject="Password Reset Request",
                    message=f"Click the link to reset your password: {reset_link}",
                    from_email="your-email@example.com",
                    recipient_list=[email],
                    fail_silently=False,
                )

               
                return redirect('custom_password_reset')
            except CustomUser.DoesNotExist:
                messages.error(request, "No account found with this email address.")
    else:
        form = CustomPasswordResetForm()

    return render(request, 'registration/custom_password_reset.html', {'form': form})
def custom_password_reset_confirm(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=user_id)
        print(f"User retrieved: {user.username} (ID: {user.id})")
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        print(f"Token valid: {default_token_generator.check_token(user, token)}")
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                print(f"Password hash after set_password: {user.password}")
                user.save()
                print(f"Password hash after saving to DB: {user.password}")

                # Double-check the database update
                updated_user = CustomUser.objects.get(pk=user.pk)
                print(f"Updated password in DB: {updated_user.password}")

                messages.success(request, "Your password has been successfully reset. You can now log in.")
                return redirect('login')
            else:
                print(f"Form errors: {form.errors}")
        else:
            form = CustomSetPasswordForm(user)

        return render(request, 'registration/custom_password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "The reset link is invalid or has expired.")
        return redirect('custom_password_reset')


