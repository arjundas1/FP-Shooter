from django import forms

class NewDoctorForm(forms.Form):
    file = forms.FileField()
