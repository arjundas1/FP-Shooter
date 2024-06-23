from django.shortcuts import render
from .forms import NewPatientForm
import tensorflow as tf
import cv2 as cv
import os
import numpy as np

IMAGE_RESIZE_X = 200  
IMAGE_RESIZE_Y = 200  
KEEP_COLOR = False 


def read_and_crop_image(image):
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    thresh = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]
    result = cv.bitwise_and(image, image, mask=thresh)
    result[thresh==0] = [255,255,255] 
    (x, y, z_) = np.where(result > 0)
    mnx = (np.min(x))
    mxx = (np.max(x))
    mny = (np.min(y))
    mxy = (np.max(y))
    crop_img = image[mnx:mxx,mny:mxy,:]
    border_v = 0
    border_h = 0
    if (IMAGE_RESIZE_Y/IMAGE_RESIZE_X) >= (crop_img.shape[0]/crop_img.shape[1]):
        border_v = int((((IMAGE_RESIZE_Y/IMAGE_RESIZE_X)*crop_img.shape[1])-crop_img.shape[0])/2)
    else:
        border_h = int((((IMAGE_RESIZE_Y/IMAGE_RESIZE_X)*crop_img.shape[0])-crop_img.shape[1])/2)
    
    crop_img = cv.copyMakeBorder(crop_img, border_v, border_v, border_h, border_h, cv.BORDER_CONSTANT, 0)
    resized_image = cv.resize(crop_img, (IMAGE_RESIZE_X, IMAGE_RESIZE_Y))
    if KEEP_COLOR:
        return resized_image
    else:
        return cv.cvtColor(resized_image, cv.COLOR_BGR2GRAY)
    return resized_image


class Project():
    
    def __init__(self, im):
        self.image = im
        self.height, self.width, self.nbchannels = im.shape
        self.size = self.width*self.height

        #Mask used to set bits:1->00000001, 2->00000010 ... (using OR gate)
        self.maskONEValues = [1<<0, 1<<1, 1<<2, 1<<3, 1<<4, 1<<5, 1<<6, 1<<7]
        self.maskONE = self.maskONEValues.pop(0) #remove first value as it is being used

        #Mask used to clear bits: 254->11111110, 253->11111101 ... (using AND gate)
        self.maskZEROValues = [255-(1<<i) for i in range(8)]
        self.maskZERO = self.maskZEROValues.pop(0)
        
        self.curwidth = 0  # Current width position
        self.curheight = 0 # Current height position
        self.curchan = 0   # Current channel position

    '''
    Function to insert bits into the image -- the actual steganography process
    param: bits - the binary values to be inserted in sequence
    '''
    def put_binary_value(self, bits):
        
        for c in bits:  #Iterate over all bits
            val = list(self.image[self.curheight,self.curwidth]) #Get the pixel value as a list (val is now a 3D array)
            if int(c):  #if bit is set, mark it in image
                val[self.curchan] = int(val[self.curchan])|self.maskONE 
            else:   #Else if bit is not set, reset it in image
                val[self.curchan] = int(val[self.curchan])&self.maskZERO 

            #Update image
            self.image[self.curheight,self.curwidth] = tuple(val)

            #Move pointer to the next space
            self.next_slot() 

    '''
    Function to move the pointer to the next location, and error handling if msg is too large
    '''
    def next_slot(self):
        if self.curchan == self.nbchannels-1: #If looped over all channels
            self.curchan = 0
            if self.curwidth == self.width-1: #Or the first channel of the next pixel of the same line
                self.curwidth = 0
                if self.curheight == self.height-1:#Or the first channel of the first pixel of the next line
                    self.curheight = 0
                    if self.maskONE == 128: #final mask, indicating all bits used up
                        raise SteganographyException("No available slot remaining (image filled)")
                    else: #else go to next bitmask
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight +=1
            else:
                self.curwidth +=1
        else:
            self.curchan +=1

    '''
    Function to read in a bit from the image, at a certain [height,width][channel]
    '''
    def read_bit(self): #Read a single bit int the image
        val = self.image[self.curheight,self.curwidth][self.curchan]
        val = int(val) & self.maskONE
        #move pointer to next location after reading in bit
        self.next_slot()

        #Check if corresp bitmask and val have same set bit
        if val > 0:
            return "1"
        else:
            return "0"
    
    def read_byte(self):
        return self.read_bits(8)

    '''
    Function to read nb number of bits
    Returns image binary data and checks if current bit was masked with 1
    '''
    def read_bits(self, nb): 
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    #Function to generate the byte value of an int and return it
    def byteValue(self, val):
        return self.binary_value(val, 8)

    #Function that returns the binary value of an int as a byte
    def binary_value(self, val, bitsize):
        #Extract binary equivalent
        binval = bin(val)[2:]

        #Check if out-of-bounds
        if len(binval)>bitsize:
            raise SteganographyException("Binary value larger than the expected size, catastrophic failure.")

        #Making it 8-bit by prefixing with zeroes
        while len(binval) < bitsize:
            binval = "0"+binval
            
        return binval

    def encode_text(self, txt):
        l = len(txt)
        binl = self.binary_value(l, 16) #Generates 4 byte binary value of the length of the secret msg
        self.put_binary_value(binl) #Put text length coded on 4 bytes
        for char in txt: #And put all the chars
            c = ord(char)
            self.put_binary_value(self.byteValue(c))
        return self.image
       
    def decode_text(self):
        ls = self.read_bits(16) #Read the text size in bytes
        l = int(ls,2)   #Returns decimal value ls
        i = 0
        unhideTxt = ""
        while i < l: #Read all bytes of the text
            tmp = self.read_byte() #So one byte
            i += 1
            unhideTxt += chr(int(tmp,2)) #Every chars concatenated to str
        return unhideTxt

# Create your views here.

def saveLocalFile(f ,fname):
    with open(f'assets/{fname}', 'wb') as localFile:
        for chunk in f.chunks():
            localFile.write(chunk)

def classify(f):
    model = tf.keras.models.load_model(os.getcwd()+"\\new_model.h5")
    img = cv.imread(f)
    changed_img = read_and_crop_image(img)
    X = np.stack(changed_img, axis=0)
    if not KEEP_COLOR:
        X = np.expand_dims(X, axis=-1)
    X = np.expand_dims(X, 0)
    X = X / 255.0
    ans = model.predict(X)
    ans = str(ans[0][0]).replace("[","")
    ans = ans.replace("]", "")
    return ans

def encrypt(msg):
    img = cv.imread(os.getcwd()+r"\assets\\"+str(file))
    obj = Project(img)
    test_img = obj.encode_text(msg)
    return test_img

def index(request):
    if request.method == 'POST':
        _formData = NewPatientForm(request.POST, request.FILES)
        if _formData.is_valid():
            global file
            file = _formData.cleaned_data["file"]
            saveLocalFile(request.FILES["file"], file)
            f = os.getcwd()+r"\assets\\"+str(file)
            cv.imwrite(os.getcwd()+r"\patient\\static\\patient\\"+str(file).split(".")[0]+".png",encrypt(classify(f)))
            
            return render(request, 'patient/index.html', context={
                'showDownload': True,
                'form': NewPatientForm(),
                'fname': str(file).split(".")[0]+".png"
            })

    return render(request, 'patient/index.html', {
        'showDownload': False,
        'form': NewPatientForm()
    })