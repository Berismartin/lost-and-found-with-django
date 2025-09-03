from django import forms
from .models import Item, ItemImage
from .models import Comment


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget for multiple file uploads"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Custom field for multiple file uploads"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Handle single file or multiple files
        if isinstance(data, (list, tuple)):
            result = [super(MultipleFileField, self).clean(d, initial) for d in data]
        else:
            result = super(MultipleFileField, self).clean(data, initial)
        return result


class ItemForm(forms.ModelForm):
    """Form for creating and updating items"""
    
    date_lost_found = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        }),
        help_text="When was this item lost or found?"
    )
    
    additional_images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*',
            'id': 'additional-images'
        }),
        help_text="Upload multiple additional images (optional)"
    )

    class Meta:
        model = Item
        fields = [
            'title', 'description', 'category', 'status', 'image',
            'location_lost_found', 'date_lost_found', 'contact_info'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter item title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe the item in detail...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'location_lost_found': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where was this item lost or found?'
            }),
            'contact_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional contact information or instructions...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make contact_info and location optional
        self.fields['contact_info'].required = False
        self.fields['location_lost_found'].required = False
        self.fields['image'].required = False
        
        # Add help text
        self.fields['title'].help_text = "Give your item a clear, descriptive title"
        self.fields['description'].help_text = "Provide as much detail as possible to help identify the item"
        self.fields['category'].help_text = "Select the category that best describes your item"
        self.fields['status'].help_text = "Is this item lost or found?"
        self.fields['image'].help_text = "Upload the main photo of the item (optional but recommended)"



class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]  # Only need the text of the comment
        widgets = {
            "content": forms.Textarea(attrs={
                "placeholder": "Write a comment...",
                "rows": 2,
                "cols": 40,
                "class": "form-control"
            }),
        }
        labels = {
            "content": ""
        }