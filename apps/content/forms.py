from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "federation", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
