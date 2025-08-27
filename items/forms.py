from django import forms
from .models import Item


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
        self.fields['image'].help_text = "Upload a clear photo of the item (optional but recommended)"
