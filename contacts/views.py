from django.shortcuts import render

# Create your views here.

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Contact

@csrf_exempt  # Disables CSRF for this endpoint for testing purposes; remove in production
def identify(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    
    email = data.get('email')
    phoneNumber = data.get('phoneNumber')
    
    # Validate at least one field is provided
    if not email and not phoneNumber:
        return JsonResponse({'error': 'Something went wrong.'}, status=400)
    
    # Query for contacts with matching email or phone number
    contacts = Contact.objects.filter(Q(email=email) | Q(phoneNumber=phoneNumber))
    
    if not contacts.exists():
        # No match: Create a new primary contact
        contact = Contact.objects.create(
            email=email,
            phoneNumber=phoneNumber,
            linkPrecedence='primary'
        )
        primary_contact = contact
    else:
        # Identify the primary contact
        primary_contacts = contacts.filter(linkPrecedence='primary')
        if primary_contacts.exists():
            primary_contact = primary_contacts.order_by('createdAt').first()
        else:
            primary_contact = contacts.order_by('createdAt').first()
        
        # Check if new information is provided
        existing_emails = {c.email for c in contacts if c.email}
        existing_phones = {c.phoneNumber for c in contacts if c.phoneNumber}
        new_info = False
        
        if email and email not in existing_emails:
            new_info = True
        if phoneNumber and phoneNumber not in existing_phones:
            new_info = True
        
        if new_info:
            # Create a new secondary contact linked to the primary
            Contact.objects.create(
                email=email,
                phoneNumber=phoneNumber,
                linkPrecedence='secondary',
                linkedId=primary_contact
            )
    
    # Consolidate all contacts linked to the primary
    all_contacts = Contact.objects.filter(Q(id=primary_contact.id) | Q(linkedId=primary_contact))
    
    emails = list({c.email for c in all_contacts if c.email})
    phoneNumbers = list({c.phoneNumber for c in all_contacts if c.phoneNumber})
    secondaryContactIds = [c.id for c in all_contacts if c.linkPrecedence == 'secondary']
    
    response_data = {
        'primaryContactId': primary_contact.id,
        'emails': emails,
        'phoneNumbers': phoneNumbers,
        'secondaryContactIds': secondaryContactIds
    }
    return JsonResponse(response_data, status=200)

