from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('foster', 'Foster Home'),
        ('adopter', 'Adopter'),
        ('admin', 'Admin'),
    ]

    full_name = models.CharField(
        max_length=150,
        default='Unknown',
        blank=False,
        help_text="Enter your full name."
    )
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)  # Defaults to True for all users except fosters
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='adopter')
    phone_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[
            RegexValidator(r'^\d{10}$', 'Only digits are allowed, and it must be exactly 10 digits.')
        ],
        help_text="Enter a valid 10-digit phone number."
    )
    license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Required if registering as a foster."
    )

    def save(self, *args, **kwargs):
        # Automatically set is_active to False for foster users
        if self.role == 'foster' and not self.pk:  # New foster user
            self.is_active = False
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def clean(self):
        # Ensure license_number is required for foster role
        if self.role == 'foster' and not self.license_number:
            raise ValidationError({'license_number': "License number is required for fosters."})
        
        # Ensure username and email are unique
        if CustomUser.objects.filter(username=self.username).exclude(pk=self.pk).exists():
            raise ValidationError({'username': "This username is already taken."})
        if CustomUser.objects.filter(email=self.email).exclude(pk=self.pk).exists():
            raise ValidationError({'email': "This email address is already taken."})

        super().clean()
