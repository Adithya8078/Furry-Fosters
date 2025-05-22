from django.db import models
from accounts.models import CustomUser


class Payment(models.Model):
    order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    upi_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Payment {self.order_id}"


class Pet(models.Model):
    CATEGORIES = [
        ('Dog', 'Dog'),
        ('Cat', 'Cat'),
        ('Bird', 'Bird'),
    ]
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    gender = models.CharField(max_length=10, default='Male')
    health_status = models.CharField(max_length=100, default="Healthy")
    availability = models.BooleanField(default=True)
    foster_home = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="fostered_pets", null=True, blank=True)
    vaccine_report = models.FileField(upload_to='vaccine_report/', null=True)
    image = models.ImageField(upload_to='petimages/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORIES, default='Dog')
    about = models.TextField(null=True, blank=True)  # New field for pet description
    location = models.CharField(max_length=255, null=True, blank=True)  # New field for pet location

    def __str__(self):
        return self.name


class Request(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="contact_requests")
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="contact_requests")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    request_date = models.DateTimeField(auto_now_add=True)

    # New fields for adopter's form responses
    intent = models.TextField(null=True, blank=True)
    experience = models.CharField(max_length=20, null=True, blank=True)
    home_environment = models.TextField(null=True, blank=True)
    
    class Meta:
        constraints = [
            # Only enforce uniqueness for non-rejected requests
            models.UniqueConstraint(
                fields=['user', 'pet'],
                condition=models.Q(status__in=['Pending', 'Approved']),
                name='unique_active_request'
            )
        ]
    def __str__(self):
        return f"Request by {self.user.username} for {self.pet.name} - {self.status}"


class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="cart")
    requests = models.ManyToManyField(Request, related_name="cart_requests")

    def __str__(self):
        return f"Cart for {self.user.username}"


class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='pet_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} about {self.pet.name}"
