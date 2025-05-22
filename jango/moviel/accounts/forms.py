from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from .models import CustomUser



class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['full_name','username', 'email', 'password1', 'password2', 'role', 'phone_number', 'license_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove 'admin' from the role choices
        self.fields['role'].choices = [
            choice for choice in self.fields['role'].choices if choice[0] != 'admin'
        ]

    def clean_license_number(self):
        license_number = self.cleaned_data.get('license_number')
        role = self.cleaned_data.get('role')

        if role == 'foster' and not license_number:
            raise forms.ValidationError("License number is required for foster users.")
        return license_number
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone_number

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email Address",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        }),
    )

class CustomSetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        user = super().save(commit=False)
        # Hash and set the new password
        user.set_password(self.cleaned_data["new_password1"])
        if commit:
            user.save()
        return user

  