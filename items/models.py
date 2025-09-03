from django.db import models
from django.conf import settings
from PIL import Image
import os


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
        ('returned_to_owner', 'Returned to Owner'),
        ('archived', 'Archived'),
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

    @property
    def main_image(self):
        """Return the main image (either the legacy image field or first ItemImage)"""
        if self.image:
            return self.image
        first_item_image = self.item_images.first()
        return first_item_image.image if first_item_image else None

    def get_all_images(self):
        """Return all images for this item (legacy + ItemImage objects)"""
        images = []
        if self.image:
            images.append(self.image)
        images.extend([img.image for img in self.item_images.all()])
        return images


class ItemImage(models.Model):
    """
    Model for storing multiple images per item
    """
    item = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE, 
        related_name='item_images'
    )
    image = models.ImageField(
        upload_to='item_images/',
        help_text="Additional image for this item"
    )
    caption = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Optional caption for this image"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order for this image"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.item.title} ({self.order})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Resize image if it exists
        if self.image:
            try:
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception:
                pass  # If PIL fails, continue without resizing

    def delete(self, *args, **kwargs):
        # Delete the image file when the model instance is deleted
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)


class Report(models.Model):
    """
    Model for reporting inappropriate or fraudulent items
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.TextField(help_text="Describe the issue or reason for reporting this item.")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report for {self.item.title} by {self.reporter.username}"

   
    


class Comment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='comments')
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.item.name}"
