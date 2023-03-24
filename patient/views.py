from django.shortcuts import render

from .forms import NewPatientForm

# Create your views here.

def saveLocalFile(f ,fname):
    with open(f'assets/{fname}', 'wb') as localFile:
        for chunk in f.chunks():
            localFile.write(chunk)

def classify(file=None):
    return "Hello, World!"

def encrypt(_string_):
    return _string_

def index(request):
    if request.method == 'POST':
        _formData = NewPatientForm(request.POST, request.FILES)
        if _formData.is_valid():

            file = _formData.cleaned_data["file"]
            saveLocalFile(request.FILES["file"], file)

            # with open('patient/static/patient/dummy.png', 'r') as file:
            #     encrypt(classify(file)) # --> Image

            img_name = 'dummy.png'
            
            return render(request, 'patient/index.html', context={
                'showDownload': True,
                'form': NewPatientForm(),
                'fname': img_name
            })

    return render(request, 'patient/index.html', {
        'showDownload': False,
        'form': NewPatientForm()
    })