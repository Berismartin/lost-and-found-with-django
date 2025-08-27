from django.db import models
from django.conf import settings
from PIL import Image


class Item(models.Model):
    """
    Item model for lost and found items
    """
    CATEGORY_CHOICES = [
        ('electronics', 'Electronics'),
        ('clothing', 'Clothing'),
        ('jewelry', 'Jewelry'),
        ('documents', 'Documents'),
        ('keys', 'Keys'),
        ('bags', 'Bags'),
        ('books', 'Books'),
        ('sports', 'Sports Equipment'),
        ('toys', 'Toys'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('lost', 'Lost'),
        ('found', 'Found'),
        ('claimed', 'Claimed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='lost')
    image = models.ImageField(
        upload_to='item_images/', 
        blank=True, 
        null=True,
        help_text="Upload an image of the item"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='items'
    )
    location_lost_found = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Where was this item lost or found?"
    )
    date_lost_found = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="When was this item lost or found?"
    )
    contact_info = models.TextField(
        blank=True,
        help_text="Additional contact information or instructions"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_status_display()}: {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize item image if it exists
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception:
                pass  # If PIL fails, continue without resizing
