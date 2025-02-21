from django.db import models

# Create your models here.

from django.db import models

class Contact(models.Model):
    LINK_PRECEDENCE_CHOICES = (
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
    )

    phoneNumber = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    # Use a self-referential foreign key for linked contacts (if secondary)
    linkedId = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    linkPrecedence = models.CharField(max_length=10, choices=LINK_PRECEDENCE_CHOICES, default='primary')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    deletedAt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Contact {self.id} ({self.linkPrecedence})"

