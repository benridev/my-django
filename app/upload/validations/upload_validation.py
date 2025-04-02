from django import forms

class MyValidationForm(forms.Form):
    image_file = forms.ImageField(required=True)
    hex_color = forms.CharField()