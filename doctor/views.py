from django.shortcuts import render
from .forms import NewDoctorForm
import cv2
import docopt
import numpy as np
import os

class Project():

    def __init__(self, im):
        self.image = im
        self.height, self.width, self.nbchannels = im.shape
        self.size = self.width*self.height
        self.maskONEValues = [1<<0, 1<<1, 1<<2, 1<<3, 1<<4, 1<<5, 1<<6, 1<<7]
        self.maskONE = self.maskONEValues.pop(0) 
        
        self.maskZEROValues = [255-(1<<i) for i in range(8)]
        self.maskZERO = self.maskZEROValues.pop(0)
        
        self.curwidth = 0  
        self.curheight = 0 
        self.curchan = 0  

    def put_binary_value(self, bits):
        
        for c in bits:  
            val = list(self.image[self.curheight,self.curwidth]) 
            if int(c):  
                val[self.curchan] = int(val[self.curchan])|self.maskONE 
            else:
                val[self.curchan] = int(val[self.curchan])&self.maskZERO 

            self.image[self.curheight,self.curwidth] = tuple(val)

            self.next_slot() 

    def next_slot(self):
        if self.curchan == self.nbchannels-1:
            self.curchan = 0
            if self.curwidth == self.width-1: 
                self.curwidth = 0
                if self.curheight == self.height-1:
                    self.curheight = 0
                    if self.maskONE == 128:
                        raise SteganographyException("No available slot remaining (image filled)")
                    else: 
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight +=1
            else:
                self.curwidth +=1
        else:
            self.curchan +=1

    def read_bit(self): 
        val = self.image[self.curheight,self.curwidth][self.curchan]
        val = int(val) & self.maskONE

        self.next_slot()

        if val > 0:
            return "1"
        else:
            return "0"
    
    def read_byte(self):
        return self.read_bits(8)

    def read_bits(self, nb): 
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    def byteValue(self, val):
        return self.binary_value(val, 8)

    def binary_value(self, val, bitsize):

        binval = bin(val)[2:]

        if len(binval)>bitsize:
            raise SteganographyException("Binary value larger than the expected size, catastrophic failure.")

        while len(binval) < bitsize:
            binval = "0"+binval
            
        return binval

    def encode_text(self, txt):
        l = len(txt)
        binl = self.binary_value(l, 16) 
        self.put_binary_value(binl) 
        for char in txt: 
            c = ord(char)
            self.put_binary_value(self.byteValue(c))
        return self.image
       
    def decode_text(self):
        ls = self.read_bits(16) 
        l = int(ls,2)   
        i = 0
        unhideTxt = ""
        while i < l: 
            tmp = self.read_byte() 
            i += 1
            unhideTxt += chr(int(tmp,2)) 
        return unhideTxt

def saveLocalFile(f ,fname):
    with open(f'assets/{fname}', 'wb') as localFile:
        for chunk in f.chunks():
            localFile.write(chunk)

def decrypt():
    path = os.getcwd()+r"\assets\\"+str(file)
    img = cv2.imread(path)
    print(img)
    obj = Project(img)
    s = "According to the model, the probability that this image indicates ALL is " + str(float(obj.decode_text())*100)+ "%"
    return s

def index(request):
    if request.method == 'POST':
        _formData = NewDoctorForm(request.POST, request.FILES)
        if _formData.is_valid():

            global file
            file = _formData.cleaned_data["file"]
            saveLocalFile(request.FILES["file"], file)
            ####
            
            return render(request, 'doctor/index.html', context={
                'showButton': True,
                'showAnalysis': False,
                'form': NewDoctorForm()
            })

    return render(request, 'doctor/index.html', {
        'showButton': False,
        'showAnalysis': False,
        'form': NewDoctorForm()
    })


def analyze(request):
    analyzed = decrypt()
    return render(request, "doctor/index.html", {
        'data': analyzed,
        'showButton': False,
        'showAnalysis': True,
        'form': NewDoctorForm()
    })