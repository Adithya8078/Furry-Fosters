
from django import forms
from .models import Pet,Message,CustomUser
class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            'name', 
            'breed', 
            'age', 
            'price', 
            'gender', 
             # Added vaccinated field
            'health_status', 
            'availability', 
            'vaccine_report', 
            'image', 
            'category', 
            'about', 
            'location',
        ]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the pet...'}),
            'location': forms.TextInput(attrs={'placeholder': 'Enter pet location'}),
            'gender': forms.TextInput(attrs={'placeholder': 'Enter gender (e.g., Male or Female)'}),
            'price': forms.NumberInput(attrs={'placeholder': 'Enter price'}),
            
        }
        labels = {
            'about': 'Description',
            'location': 'Pet Location',
            'gender': 'Gender',
            'vaccinated': 'Is the pet vaccinated?',
            'price': 'Adoption Price',
        }

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age > 15:
            raise forms.ValidationError('Age cannot be greater than 15.')
        return age



class AdoptionIntentForm(forms.Form):
    intent = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Why do you want to adopt this pet?', 'rows': 3}),
        label="Why do you want to adopt this pet?",
        required=True
    )
    experience = forms.ChoiceField(
        choices=[('Yes', 'Yes'), ('No', 'No')],
        widget=forms.Select(attrs={'placeholder': 'Do you have experience caring for pets?'}),
        label="Do you have experience caring for pets?",
        required=True
    )
    home_environment = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Describe your home environment', 'rows': 3}),
        label="Describe your home environment",
        required=True
    )
class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Write your message here...',
                'rows': 4
            })
        }
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['full_name','username', 'email', 'phone_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'