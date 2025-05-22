from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.db.models import Max
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from django.db import transaction
import io
import base64
import uuid
from decimal import Decimal
from io import BytesIO
from base64 import b64encode
from accounts.models import CustomUser
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from movielapp.models import Cart, Pet,Request,Message,Payment
from django.contrib import messages
from .forms import PetForm,AdoptionIntentForm,UserProfileForm
from django.db.models import Q
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.template.loader import render_to_string

from django.http import HttpResponse
def role_based_redirect(request):
    if not request.user.is_authenticated:
        return redirect('/home')
    
    # Redirect users based on their role
    elif request.user.is_authenticated and request.user.role == 'foster':
        return redirect(f'/foster/{request.user.id}/')
    
    elif request.user.is_authenticated and request.user.role == 'adopter':
        return redirect('/home')  # Fixed the extra redirect()

    elif request.user.is_authenticated and request.user.role == 'admin':
        return redirect(f'/custom-admin/{request.user.id}/')

    return redirect('/home')


def house(request):
    query = request.GET.get('query', '')
    if query:
        pets = Pet.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(breed__icontains=query) |
            Q(health_status__icontains=query) |
            Q(location__icontains=query),
            availability=True
        )[:6]
    else:
        pets = Pet.objects.filter(availability=True)[:6]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('homepage/pet_form.html', {
            'pets': pets,
            'query': query
        })
        return JsonResponse({
            'html': html,
            'count': pets.count()
        })

    return render(request, 'homepage/home.html', {
        'pets': pets,
        'query': query
    })
@login_required

def adopter_page(request, user_id):
    # Adopter-specific logic
    if request.user.id != user_id or request.user.role != 'adopter':
        return redirect('/home')
    pets = Pet.objects.all()
    return render(request, 'homepage/home.html',{'pets': pets})

@login_required

def add_pet(request):
    # Adding a pet (for foster role)
    if request.method == 'POST':
        form = PetForm(request.POST,request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.foster_home = request.user
            pet.save()
            return JsonResponse({'success': True})
    else:
        form = PetForm()
    return render(request, 'pets/pet_form.html', {'form': form})
@login_required
@never_cache
def admin_page(request, user_id):
    if request.user.id != user_id or request.user.role != 'admin':
        return redirect('/home')
    users = CustomUser.objects.all().order_by('last_login')
    pets = Pet.objects.all()
    approved_requests = Request.objects.filter(status="Approved").order_by('-request_date')
    return render(request, 'admin_page.html', {
        'users': users,
        'pets': pets,
        'approved_requests': approved_requests,
    })
@login_required
@never_cache
def edit_user(request, user_id):
    # Placeholder for editing user functionality
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'edit_user.html', {'user': user})
@login_required
@never_cache
def delete_user(request, user_id):
    if not request.user.is_superuser:  # Only allow superusers to delete users
        return redirect('home')

    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_superuser:
        return redirect('admin_page')  # Prevent deletion of superusers

    user.delete()
    return HttpResponseRedirect(reverse('admin_page', args=[request.user.id]))
@login_required
@never_cache
def edit_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)

    # Only allow foster home users to edit pets they own
    if request.user.role != 'foster' or pet.foster_home != request.user:
        return redirect('home')

    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('foster_page', args=[request.user.id]))
    else:
        form = PetForm(instance=pet)
    
    return render(request, 'pets/edit_pet.html', {'form': form})
@login_required
@never_cache

@login_required    
def about(request):
    return render(request, 'homepage/about.html')


@login_required
@never_cache
def category_view(request, category):
    normalized_category = category.capitalize()  # Capitalize the first letter
    pets = Pet.objects.filter(category=normalized_category)
    context = {
        'animal': normalized_category,
        'pets': pets,
    }
    return render(request, 'homepage/category.html', context)
@login_required
@never_cache
def foster_page(request, user_id):
    if request.user.id != user_id or request.user.role != 'foster':
        return redirect('/home')
   
    pets = request.user.fostered_pets.all()
    requests = Request.objects.filter(
        pet__foster_home=request.user,
        status='Pending'
    ).select_related('user', 'pet')
   
    # Modified to match pet_detail approach
    last_messages = (
        Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        )
        .values('pet_id')  # Only group by pet_id
        .annotate(last_message_id=Max('id'))
    )
   
    last_message_ids = [msg['last_message_id'] for msg in last_messages]
    last_messages_queryset = (
        Message.objects.filter(id__in=last_message_ids)
        .select_related('sender', 'recipient', 'pet')
        .order_by('-created_at')
    )
   
    context = {
        'pets': pets,
        'requests': requests,
        'last_messages': last_messages_queryset,
        'form': PetForm(),
    }
   
    return render(request, 'foster/foster_page.html', context)
@login_required
@never_cache
def pet_detail(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    
    # Fetch both sent and received messages
    last_messages = (
        Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        )
        .values('pet_id')
        .annotate(last_message_id=Max('id'))
    )
    
    last_message_ids = [msg['last_message_id'] for msg in last_messages]
    last_messages_queryset = (
        Message.objects.filter(id__in=last_message_ids)
        .select_related('sender', 'recipient', 'pet')
        .order_by('-created_at')
    )
    
    chat_messages_queryset = Message.objects.filter(
        Q(pet=pet) &
        (Q(sender=request.user) | Q(recipient=request.user))
    ).order_by('created_at')
    
    context = {
        'pet': pet,
        'form': AdoptionIntentForm(),
        'last_messages': last_messages_queryset,
        'chat_messages': chat_messages_queryset,
    }
    return render(request, 'pets/pet_detail.html', context)


@login_required
@csrf_exempt
def create_contact_request(request, pet_id):
    if request.method == 'POST':
        pet = get_object_or_404(Pet, id=pet_id)

        # Extract form data
        intent = request.POST.get('intent')
        experience = request.POST.get('experience')
        home_environment = request.POST.get('home_environment')
        payment_id = request.POST.get('payment_id')

        # Validate payment
        payment = get_object_or_404(Payment, order_id=payment_id)
        if payment.status != 'completed':
            return JsonResponse({'success': False, 'message': 'Payment not completed.'})

        # Ensure no existing active requests
        existing_request = Request.objects.filter(user=request.user, pet=pet, status__in=['Pending', 'Approved']).first()
        if existing_request:
            return JsonResponse({'success': False, 'message': 'You already have an active request for this pet.'})

        # Create the request
        contact_request = Request.objects.create(
            user=request.user,
            pet=pet,
            payment=payment,
            intent=intent,
            experience=experience,
            home_environment=home_environment,
        )
        return JsonResponse({'success': True, 'message': 'Contact request created successfully!'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

def update_pet(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id)
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors})
    return JsonResponse({"success": False})

def delete_pet(request, pet_id):
    if request.method == "POST":
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()
        return JsonResponse({"success": True, "message": "Pet deleted successfully!"})

    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
@login_required    
def view_foster_requests(request):
    if request.user.role != 'foster':
        return JsonResponse({'success': False, 'message': 'Unauthorized access.'}, status=403)

    requests = Request.objects.filter(pet__foster_home=request.user, status="Pending")
    return render(request, 'foster/foster_page.html', {'requests': requests})
  # Replace 'Request' with your actual model name
@login_required
def update_request_status(request, request_id):
    if request.method == 'POST':
        req = get_object_or_404(Request, id=request_id)
        status = request.POST.get('status')
        
        if status == 'Rejected':
            # Mark payment for refund
            if req.payment:
                req.payment.status = 'refund'
                req.payment.save()
            
            req.status = 'Rejected'
            req.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Request rejected and payment marked for refund'
            })
            
        elif status == 'Approved':
            req.pet.availability = False
            req.pet.save()
            
            # Get other pending requests for this pet
            other_requests = Request.objects.filter(
                pet=req.pet
            ).exclude(
                id=request_id
            )
            
            # Mark payments for refund and reject other requests
            for other_req in other_requests:
                if other_req.payment:
                    other_req.payment.status = 'refund'
                    other_req.payment.save()
                other_req.status = 'Rejected'
                other_req.save()
            
            req.status = 'Approved'
            req.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Request approved successfully! Other requests were rejected with refunds.'
            })
            
    return JsonResponse({'success': False, 'message': 'Invalid request method'})



@login_required
def cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    return render(request, 'homepage/cart.html', {'cart': cart})
def pets(request):
    query = request.GET.get('query', '')
    
    if query:
        pets = Pet.objects.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(breed__icontains=query) |
            Q(health_status__icontains=query) |
            Q(location__icontains=query),
            availability=True
        )
    else:
        pets = Pet.objects.filter(availability=True)

    
    
    return render(request, 'pets/pets.html', {'pets': pets, 'query': query})
@login_required        
def adopter_details_view(request, user_id):
    adopter = get_object_or_404(CustomUser, id=user_id)
    approved_requests = Request.objects.filter(user=adopter, status='Approved')
    pets = [req.pet for req in approved_requests]
    return render(request, 'adopter/adopter_details.html', {'adopter': adopter, 'pets': pets})
@login_required
def foster_details_view(request, user_id):
    foster = get_object_or_404(CustomUser, id=user_id)
    available_pets = Pet.objects.filter(foster_home=foster, availability=True)
    return render(request, 'foster/foster_details.html', {'foster': foster, 'available_pets': available_pets})


@login_required
def fetch_chat(request, pet_id, recipient_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'})

    try:
        messages = Message.objects.filter(
            pet_id=pet_id
        ).filter(
            Q(sender=request.user, recipient_id=recipient_id) |
            Q(sender_id=recipient_id, recipient=request.user)
        ).order_by('created_at')

        message_list = [
            {
                'content': message.content,
                'sender': str(message.sender.id),
                'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            for message in messages
        ]

        # Debug log for response
        print(f"Returning {len(message_list)} messages")
        return JsonResponse({'success': True, 'messages': message_list})
    except Exception as e:
        print(f"Error fetching chat: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

def messages_view(request):
    last_messages = (
        Message.objects.filter(sender=request.user)
        .values('pet_id')
        .annotate(last_message_id=Max('id'))
    )
    messages = Message.objects.filter(id__in=[msg['last_message_id'] for msg in last_messages]).order_by('-created_at')
    print(messages)
    return render(request, 'messages/message.html',{'messages': messages})


def send_message(request, pet_id):
    if request.method == 'POST':
        content = request.POST.get('content')
        recipient_id = request.POST.get('recipient_id')

        try:
            # Save message in the database
            message = Message(
                sender=request.user,
                recipient_id=recipient_id,
                pet_id=pet_id,
                content=content,
            )
            message.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@login_required
def download_pdf(request, request_id):
    # Fetch the request object with related payment, pet, and user
    pet_request = get_object_or_404(Request, id=request_id, status='Approved')
    payment = pet_request.payment
    pet = pet_request.pet
    adopter = pet_request.user  # The adopter
    foster_home = pet.foster_home  # The foster home who uploaded the pet

    # Create a response object for the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pet.name}_payment_confirmation.pdf"'
    
    # Create the PDF object
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []
    
    # Company Header
    header_data = [
        ['Furry Fosters'],
        ['22 East 30th Place'],
        ['Bangalore, India'],
        ['Contact: +91 8760xxxxxxx'],
        ['Email: ajxxxxx@gmail.com']
    ]
    
    header_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    header_table = Table(header_data)
    header_table.setStyle(header_style)
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Date
    elements.append(Paragraph(f"Date: {payment.created_at.strftime('%d %B %Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Subject
    elements.append(Paragraph(f"Subject: Payment Confirmation for {pet.name}", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    # Confirmation Letter Content
    letter_content = f"""
    Dear {adopter.full_name},
    
    This letter confirms that we have received your payment for the adoption of {pet.name}. 
    We are delighted to inform you that your payment has been processed successfully and your adoption request 
    has been approved.
    
    Please find the detailed payment and adoption information below. For any queries or assistance, 
    please contact our support team.
    
    Thank you for choosing to adopt from Furry Fosters. We hope {pet.name} brings joy and happiness to your family.
    
    Best regards,
    Furry Fosters Team
    """
    elements.append(Paragraph(letter_content, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Common table style
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#78B79F")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    
    # Payment Information
    payment_data = [
        ['Payment Information'],
        ['Order ID', payment.order_id],
        ['Amount', f'Rs.{payment.amount}'],
        ['UPI ID', payment.upi_id],
        ['Status', payment.status],
        ['Payment Date', payment.created_at.strftime('%d %B %Y, %I:%M %p')]
    ]
    payment_table = Table(payment_data, colWidths=[200, 300])
    payment_table.setStyle(table_style)
    elements.append(payment_table)
    elements.append(Spacer(1, 20))
    
    # Adopter Information
    adopter_data = [
        ['Adopter Information'],
        ['Name', adopter.full_name],
        ['Email', adopter.email],
        ['Phone', adopter.phone_number or 'Not provided']
    ]
    adopter_table = Table(adopter_data, colWidths=[200, 300])
    adopter_table.setStyle(table_style)
    elements.append(adopter_table)
    elements.append(Spacer(1, 20))
    foster_home_data = [
        ['Recipient (Foster Home) Information'],
        ['Name', f'{foster_home.username}' if foster_home else 'N/A'],
        ['Email', foster_home.email if foster_home else 'N/A'],
        ['Phone', foster_home.phone_number if foster_home and foster_home.phone_number else 'N/A']
    ]
    foster_home_table = Table(foster_home_data,colWidths=[200,300])
    foster_home_table.setStyle(table_style)
    
    elements.append(foster_home_table)
    elements.append(Spacer(1, 20))
    # Pet Information
    pet_data = [
        ['Pet Information'],
        ['Pet Name', pet.name],
        ['Breed', pet.breed],
        ['Age', f'{pet.age} years'],
        ['Gender', pet.gender],
        ['Price', f'Rs.{pet.price}'],
        ['Health Status', pet.health_status],
        ['Category', pet.category],
        ['Location', pet.location or 'Not provided']
    ]
    pet_table = Table(pet_data, colWidths=[200, 300])
    pet_table.setStyle(table_style)
    elements.append(pet_table)
    
    # Build the PDF
    doc.build(elements)
    return response

@login_required



def profile_view(request):
    profile_form = UserProfileForm(instance=request.user)
    password_form = PasswordChangeForm(request.user)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            profile_form = UserProfileForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                username = profile_form.cleaned_data.get('username')
                email = profile_form.cleaned_data.get('email')
                phone_number = profile_form.cleaned_data.get('phone_number')

                # Check for duplicate username
                if CustomUser.objects.filter(username=username).exclude(pk=request.user.pk).exists():
                    profile_form.add_error('username', 'This username is already taken.')

                # Check for duplicate email
                if CustomUser.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                    profile_form.add_error('email', 'This email address is already taken.')

                # Check for duplicate phone number if provided
                if phone_number and CustomUser.objects.filter(phone_number=phone_number).exclude(pk=request.user.pk).exists():
                    profile_form.add_error('phone_number', 'This phone number is already taken.')

                if not profile_form.errors:
                    profile_form.save()
                    
                    return redirect('profile')
        
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                
                return redirect('profile')

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'homepage/profile.html', context)



def generate_payment_qr(request):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to continue'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=405)

    try:
        with transaction.atomic():
            pet_id = request.POST.get('pet_id')
            pet = get_object_or_404(Pet, id=pet_id)
            
            # Check for existing requests
            existing_request = Request.objects.filter(
                user=request.user,
                pet=pet,
                status__in=['Pending', 'Approved']
            ).exists()
            
            if existing_request:
                return JsonResponse({
                    'success': False,
                    'message': 'You already have an active request for this pet.'
                })
            
            # Store form data
            request.session['adoption_form_data'] = {
                'intent': request.POST.get('intent'),
                'experience': request.POST.get('experience'),
                'home_environment': request.POST.get('home_environment')
            }
            
            # Create payment record
            payment = Payment.objects.create(
                order_id=str(uuid.uuid4()),
                amount=pet.price,
                upi_id="your-merchant-upi@bank",  # Replace with actual UPI ID
                status='pending'
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            upi_data = (f"upi://pay?"
                       f"pa={payment.upi_id}&"
                       f"pn=Pet Adoption&"
                       f"am={payment.amount}&"
                       f"tr={payment.order_id}&"
                       f"tn=Adoption fee for {pet.name}")
            qr.add_data(upi_data)
            qr.make(fit=True)
            
            # Convert QR to base64
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return JsonResponse({
                'success': True,
                'qr_code': f"data:image/png;base64,{qr_base64}",
                'payment_id': payment.order_id,
                'amount': str(payment.amount)
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def validate_payment(request, payment_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to continue'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Invalid request method'
        }, status=405)

    try:
        with transaction.atomic():
            payment = get_object_or_404(Payment, order_id=payment_id)
            if payment.status == 'completed':
                return JsonResponse({
                    'success': False,
                    'message': 'Payment already processed'
                })
            
            # Update payment status
            payment.status = 'completed'
            payment.save()
            
            # Get stored form data
            form_data = request.session.get('adoption_form_data', {})
            
            # Create request
            pet_id = request.POST.get('pet_id')
            pet = get_object_or_404(Pet, id=pet_id)
            
            contact_request = Request.objects.create(
                user=request.user,
                pet=pet,
                payment=payment,
                intent=form_data.get('intent'),
                experience=form_data.get('experience'),
                home_environment=form_data.get('home_environment'),
                status='Pending'
            )
            
            # Add to cart
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart.requests.add(contact_request)
            
            # Clear session data
            if 'adoption_form_data' in request.session:
                del request.session['adoption_form_data']
            
            return JsonResponse({
                'success': True,
                'message': 'Payment validated and request created successfully!'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)