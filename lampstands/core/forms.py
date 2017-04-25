from django import forms
from .models import ChurchPage

class LocalityEntryForm(forms.ModelForm):
    class Meta:
        model = ChurchPage
        fields = ['url','id','locality_name', 'meeting_address', 'locality_state_or_province', 
            'locality_country', 'locality_phone_number', 'locality_email','locality_web']