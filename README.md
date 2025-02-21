# EMOTORAD_IDENTITY_RECONCILIATION_SERVICE

This project implements a covert web service that consolidates different email addresses and phone numbers into a single contact record. The service is designed to support a scenario in which a user (Dr. Chandrashekar, also known as Doc) uses multiple contact details to avoid detection on Zamazon.com while a partner service (Emotorad) needs to merge these details.

TECH USED- PYTHON, DJANGO, MYSQL, GIT, NOTEPAD/VISUAL STUDIO/ANY CODE EDITOR

The implementation fulfills the following assignment requirements:

1) Process JSON Payloads: Accepts an incoming JSON payload with optional "email" and "phoneNumber" fields.
2) Consolidate Contact Information: Queries the database for matching records and consolidates details into a single primary contact with linked secondary contacts.
3) Create New Contacts: If no matching contacts are found, creates a new record with linkPrecedence = "primary".
4) Link Secondary Contacts: When matching contacts exist and new information is provided, creates a secondary contact entry linked to the primary.
5) Dual-Purpose Primary/Secondary Handling: Allows primary contacts to transition into a secondary role if further overlapping information is detected.
6) Response Mechanism: Returns an HTTP 200 status with a JSON payload including primaryContactId, emails, phoneNumbers, and secondaryContactIds.

What This Project Does:

1) Collects Contact Details: Accepts an email and/or phone number.
2) Merges Information: Links multiple emails or phone numbers that belong to the same individual.
3) Returns Organized Data: Outputs a primary contact and any linked secondary contacts.
4) Visual Data Viewing: Enables data inspection via Django Admin & MySQL client.
 
Steps to Set Up the Project:

1) Install PYTHON Software: The user must download and install Python from "https://www.python.org/downloads/" . During installation, ensure that Python is added to the system PATH.

2) Install MySQL Server: The user must download and install MySQL from "https://dev.mysql.com/downloads/mysql/" . After installation, open MySQL and create a new database using: CREATE DATABASE zamazon_db;

3) Django and MySQL Client Library: The user must open a command prompt and run the two commands one by one:

pip install django
pip install mysqlclient   
#If mysqlclient fails, the user may try using mysql-connector-python instead

4) Create and Configure the Django Project: In the command prompt, run: django-admin startproject zamazon_project
           #This creates a folder named zamazon_project.

5) Create the Contacts App: Change into the project folder and create the app by writing the two command lines one by one
   
    cd zamazon_project
   
    python manage.py startapp contacts
   
6) Register the App with Django: In settings.py inside zamazon_project, add the following to the INSTALLED_APPS list:

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'contacts',
]

7) Configure the Database (MySQL): In the same settings.py file, update the DATABASES section:

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'zamazon_db',          
        'USER': 'root',     
        'PASSWORD': '#Anonymous05',  
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

8) Define the Contact Model: Create the Contact model in models.py inside contacts as follows:


from django.db import models
class Contact(models.Model):

    # Choices for link precedence: primary if first contact, secondary if linked later.
    LINK_PRECEDENCE_CHOICES = (
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
    )
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    # This field links a secondary contact to a primary contact.
    linkedId = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    linkPrecedence = models.CharField(max_length=10, choices=LINK_PRECEDENCE_CHOICES, default='primary')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    deletedAt = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        # Returns a string representation of the contact, showing its id and precedence.
        return f"Contact {self.id} ({self.linkPrecedence})"


9) Implement the /identify Endpoint: Create the view in views.py inside contacts to process POST requests at /identify/:

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Contact

@csrf_exempt  # Disables CSRF protection for testing purposes (should be enabled in production)

 def identify(request):

    # Only allow POST requests.
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed.'}, status=405)   
    try:
        # Parse the incoming JSON payload.
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    email = data.get('email')
    phoneNumber = data.get('phoneNumber') 
    # Validate that at least one field is provided.
    if not email and not phoneNumber:
        return JsonResponse({'error': 'Something went wrong.'}, status=400)    
    # Query the database for any contact matching the provided email or phone number.
    contacts = Contact.objects.filter(Q(email=email) | Q(phoneNumber=phoneNumber))    
    if not contacts.exists():
        # No matching contact: create a new primary contact.
        contact = Contact.objects.create(
            email=email,
            phoneNumber=phoneNumber,
            linkPrecedence='primary'
        )
        primary_contact = contact
    else:
        # If contacts exist, determine the primary contact.
        primary_contacts = contacts.filter(linkPrecedence='primary')
        if primary_contacts.exists():
            primary_contact = primary_contacts.order_by('createdAt').first()
        else:
            primary_contact = contacts.order_by('createdAt').first()        
        # Check if the incoming request introduces new information.
        existing_emails = {c.email for c in contacts if c.email}
        existing_phones = {c.phoneNumber for c in contacts if c.phoneNumber}
        new_info = False        
        if email and email not in existing_emails:
            new_info = True
        if phoneNumber and phoneNumber not in existing_phones:
            new_info = True    
        if new_info:
            # New information found: create a secondary contact linked to the primary.
            Contact.objects.create(
                email=email,
                phoneNumber=phoneNumber,
                linkPrecedence='secondary',
                linkedId=primary_contact
            )  
    # Consolidate all contacts linked to the primary, fulfilling the requirement
    # for returning a unified view of contact details.
    all_contacts = Contact.objects.filter(Q(id=primary_contact.id) | Q(linkedId=primary_contact))
    emails = list({c.email for c in all_contacts if c.email})
    phoneNumbers = list({c.phoneNumber for c in all_contacts if c.phoneNumber})
    secondaryContactIds = [c.id for c in all_contacts if c.linkPrecedence == 'secondary']   
    # Construct the response payload as required.
    response_data = {
        'primaryContactId': primary_contact.id,
        'emails': emails,
        'phoneNumbers': phoneNumbers,
        'secondaryContactIds': secondaryContactIds
    }
    return JsonResponse(response_data, status=200)

10) Configure URLs: In the Contacts App, create a file named urls.py inside the contacts app (if it does not exist) with the following content:

from django.urls import path
from .views import identify

urlpatterns = [
    path('identify/', identify, name='identify'),
]

11) In the Main Project, edit urls.py inside amazon_project to include the contacts app’s URLs:

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('contacts.urls')), 
]

12) Register the Contact Model in the Admin Panel: In admin.py inside contacts, register the model to enable data management through Django Admin:

from django.contrib import admin

from .models import Contact

admin.site.register(Contact)

13) Migrate the Database and Create a Superuser:
   
13.1.) In the command prompt (in the same directory as manage.py), run:

python manage.py makemigrations

python manage.py migrate

13.2) Create an Admin User, Run: python manage.py createsuperuser 
      #The user must follow the prompts to set up a username, email, and password. (Note: the password input will be hidden for security.) (for eg. username: prakh ; email: prakhar.s4298@gmail.com ; password: prakharsinghania

14) Running the Django Development Server, Run: python manage.py runserver
    #The user will see a message such as: Starting development server at http://127.0.0.1:8000/
    
15) Testing the /identify Endpoint, Using cURL: Open a new command prompt (while the server is running) and execute:
    
    curl -X POST -H "Content-Type: application/json" -d "{\"email\":\"ps@mail.com\", \"phoneNumber\":\"1234567890\"}" http://127.0.0.1:8000/identify/
    
   '''  The expected JSON response should be:

{
  "primaryContactId": 1,
  "emails": ["ps@mail.com"],
  "phoneNumbers": ["1234567890"],
  "secondaryContactIds": []
} 

 This confirms that the service correctly creates and links contact records according to the assignment requirements.
 Can take inputs from the user by editing the email and the phoneNumber section by the required data and run the cURL command for data entries. '''

16) Viewing Data
    
16.1) Via Django Admin: Open http://127.0.0.1:8000/admin/ in browser. Log in with the superuser credentials. Click on "Contacts" to view the list of contact records.

16.2) Via a MySQL Client: Download and install MySQL Workbench from "https://dev.mysql.com/downloads/workbench/". Connect to the database using localhost and port 3306. Locate the zamazon_db schema and open the table contacts_contact to view the stored data.


Assignment Requirements Fulfillment:

1) Process JSON payloads	The /identify endpoint accepts and validates JSON with optional "email" and "phoneNumber".	✓
2) Consolidate Contact Information	The service consolidates records and returns primaryContactId, emails, phoneNumbers, and secondaryContactIds.	✓
3) Create New Contact on No Match	A new contact record is created with linkPrecedence = "primary" when no matches are found.	✓
4) Create Secondary on Match with New Info	When matching contacts exist but new info is provided, a new record is added as secondary.	✓
5) Primary to Secondary Transformation	The logic supports a primary contact being linked to additional secondary records.	✓
6) Error Handling and Bonus Points	Basic error responses are implemented; additional covert error handling and testing strategies can be added as needed.	Partially ✓


