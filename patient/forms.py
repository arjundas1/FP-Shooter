from django import forms

class NewPatientForm(forms.Form):
    file = forms.FileField()
