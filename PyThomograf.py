import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.color import gray2rgb
import copy
import math
import os
import tkinter as tk
from tkinter import ttk
import pydicom
from tkinter import filedialog
import pydicom.uid
from tkcalendar import Calendar
from datetime import datetime
from pydicom.uid import SecondaryCaptureImageStorage
import pydicom
from pydicom.dataset import Dataset, FileDataset
from sklearn.metrics import mean_squared_error
from time import sleep

def Bresenham(x0,y0,x1,y1):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    points = []
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        err2 = err * 2
        if err2 > -dy:
            err -= dy
            x0 += sx
        if err2 < dx:
            err += dx
            y0 += sy


    return zip(*points)
#TRZEBA dodać porównanie błędu średniokwadratowego dla obrazu wejsciowego i zrekonstruowanego 
#Dla roznych wartosci parametrow 
#o zmianę błędu średniokwadratowego przy zwiększaniu dokładności
#próbkowania (trzy uprzednio wymienione parametry modelu emiter/detektor),

def bladSrednioKwadratowy(RMSEList,image_empty,image):
    normImage = image_empty.copy()
    normImage -= np.min(normImage)
    if np.max(normImage) != 0:
        normImage /= np.max(normImage)
    normImage *= 255
    normImage = normImage.astype(np.uint8)

    mse = mean_squared_error(image.flatten(), normImage.flatten())
    rmse = np.sqrt(mse)
    RMSEList.append(rmse)
    return RMSEList

def rekonstruct(image_empty, sinogram, alpha, r, centerx, centery, filter, steps, n, l,image):

    liczbaEm = n
    if filter:
        RMSEListFiltered = []
    else:
        RMSEList = []

    if(filter):
        filtered_sinogram = []
        for projection in sinogram:
            filtered_projection = filtr(projection)
            filtered_sinogram.append(filtered_projection)
        plt.figure(figsize=(10, 5))
        plt.imshow(filtered_sinogram, cmap='gray')
        plt.title("Sinogram po filtracji")
        plt.xlabel("Pozycja detektora (kąty)")
        plt.ylabel("Pozycja detektora (projekcje)")
        plt.colorbar(label="Suma wartości pikseli")
        plt.show()
        filtered_sinogram = np.array(filtered_sinogram)
        sinogram = filtered_sinogram
    num_angles = sinogram.shape[0]
    for j in range(num_angles):
        angle = j * alpha 
        for i in range(liczbaEm):
            # Obliczanie pozycji sensora
            # pos = (i - liczbaEm / 2) / 2
            pos = (i*l/liczbaEm-l/2)

            # Używamy tych samych wzorów jak przy generowaniu sinogramu:
            start = (r * np.cos(np.radians(pos + angle)) + centerx,
                    r * np.sin(np.radians(pos + angle)) + centery)
            end = (r * (-np.cos(np.radians(-pos + angle))) + centerx,
                r * (-np.sin(np.radians(-pos + angle))) + centery)
            
            # Pobranie punktów na linii wykorzystując funkcję Bresenham
            rr_cc = list(Bresenham(int(start[0]), int(start[1]), int(end[0]), int(end[1])))
            if not rr_cc:
                continue
            # Rozpakowanie współrzędnych i konwersja na tablice NumPy
            rr = np.array(rr_cc[0])
            cc = np.array(rr_cc[1])
            # Upewnienie się, że indeksy mieszczą się w zakresie obrazu
            rr = np.clip(rr, 0, image_empty.shape[0] - 1)
            cc = np.clip(cc, 0, image_empty.shape[1] - 1)
            
            # Backprojection: dodajemy wartość z sinogramu do wszystkich punktów linii
            image_empty[rr, cc] += sinogram[j, i]
        
        #Liczenie bledu sredniokwadratowego
        if filter:
            RMSEListFiltered = bladSrednioKwadratowy(RMSEListFiltered,image_empty,image)
        else:
            RMSEList = bladSrednioKwadratowy(RMSEList,image_empty,image)
        

        if steps:
            plt.imshow(image_empty, cmap='gray')
            plt.title(f"Krok pośredni rekonstrukcji: kąt {j * alpha}°")
            plt.axis("off")
            plt.pause(0.01)
            plt.clf()
    # Normalizacja zrekonstruowanego obrazu do zakresu 0-255
    image_empty -= np.min(image_empty)
    if np.max(image_empty) != 0:
        image_empty /= np.max(image_empty)
    image_empty *= 255
    if filter:
        return image_empty.astype(np.uint8),RMSEListFiltered
    else: 
        return image_empty.astype(np.uint8),RMSEList
        
def filtr(sinogram):
    wielkosc = len(sinogram)
    mask = []
    for k in range(-wielkosc//2,wielkosc//2 +1):
        if k == 0:
            mask.append(1)
        else:
            if k % 2 == 0:
                mask.append(0)
            else:
                mask.append((-4/(math.pi**2))/k**2)
    
    mask = np.array(mask)
    
    hamm_window = np.hamming(len(mask))
    mask *= hamm_window

    mask /= np.sum(np.abs(mask))

    filtered = np.convolve(sinogram, mask, mode='same')
    return filtered

def createSinogram(image, centerx,centery,height,width,r, filter,steps,n,l,alpha,dicom):

    scan_1d_values = []
    liczbaEm=n
    deep=copy.deepcopy(image)
    sleep(2)
    for j in np.arange(0, 181,alpha):#Ustawienie detektorow
        emitter_scan = []
        image_copy = gray2rgb(deep)
        for i in range(0, liczbaEm):#Polozenie jednego detektora dla danego ustawienia detektorow
            pos = (i*l/liczbaEm-l/2)

            start = (r * np.cos(np.radians(pos + j))+centerx, r * np.sin(np.radians(pos + j))+centery)
            end = (r * (-1*np.cos(np.radians(-pos +j)))+centerx,r * (-1*np.sin(np.radians(-pos + j)))+centery)
            rr, cc = Bresenham(int(start[0]), int(start[1]), int(end[0]), int(end[1]))
            rr = np.clip(rr, 0, height - 1)
            cc = np.clip(cc, 0, width - 1)

            Values = image[rr,cc]
            Intensity = np.sum(Values)

            emitter_scan.append(Intensity)


            if(steps):
                image_copy[centerx,centery]=[int(255),0,0]
                for test in range(-5,5):
                    image_copy[centerx+test,centery]=[int(255),0,0]
                    image_copy[centerx+test,centery+test]=[int(255),0,0]
                    image_copy[centerx,centery+test]=[int(255),0,0]
                if(pos==0):
                    image_copy[rr, cc] = [0, 255, 0]
                else:
                    image_copy[rr, cc] = [255,255,255]

        if(steps): #Co piąty wyswietla do przyspieszenia do kodu
            plt.imshow(image_copy)
            plt.title(f"Linia dla j={round(j,0)}")
            plt.axis("off")
            plt.pause(0.001)
            plt.clf()



        scan_1d_values.append(emitter_scan)



    plt.figure(figsize=(10, 5))
    plt.imshow(scan_1d_values, cmap='gray')
    plt.title("Sinogram")
    plt.xlabel("Pozycja detektora (kąty)")
    plt.ylabel("Pozycja detektora (projekcje)")
    plt.colorbar(label="Suma wartości pikseli")
    plt.show()

    image_empty = np.zeros((image.shape[0],image.shape[1]),dtype=float)
    copy2 = copy.deepcopy(image)
    if filter:
        copy2,RMSEListFiltered = rekonstruct(image_empty, np.array(scan_1d_values), alpha, r, centerx, centery, filter, steps,n,l,image)
    else:
        copy2,RMSEList = rekonstruct(image_empty, np.array(scan_1d_values), alpha, r, centerx, centery, filter, steps,n,l,image)
    if dicom:
        saveDicom(copy2,filename = imageChoiceDicom.get())
    # plt.figure(figsize=(8, 8))

    plt.imshow(copy2,cmap="gray")
    plt.colorbar()
    plt.show()
    if filter:
        return RMSEListFiltered
    else:
        return RMSEList
#KWADRATY
# image = imread("Kolo.jpg")# ✅  
# image = imread("Kropka.jpg")# ✅
# image = imread("Kwadraty2.jpg")#✅
# image = imread("Paski2.jpg")#❌ #Caly czarny obraz
# image = imread("Shepp_logan.jpg")#✅ Nieco wyblakle
#PROSTOKATY
# image = imread("CT_ScoutView-large.jpg")#✅
# image = imread("CT_ScoutView.jpg")#✅

# image = imread("SADDLE_PE-large.jpg")#✅ Nieco wyblakle
# image = imread("SADDLE_PE.jpg")#❌ -> caly czarny obraz

def RMSEChart(RMSEList,Usefilter):
    print("OSTATNI:",RMSEList[-1])
    plt.scatter(range(len(RMSEList)), RMSEList, s = 5)
    plt.xlabel("Iteracja (kąt)")
    plt.ylabel("Błąd średniokwadratowy (RMSE)")
    if Usefilter:
        plt.title("Zmiana błędu RMSE w czasie rekonstrukcji przy uzyciu filtrowanego sinogramu")
    else:
        plt.title("Zmiana błędu RMSE w czasie rekonstrukcji bez filtrowania sinogramu")
    plt.show()

def app(image, dicom=False):
    height,width = image.shape[:2]
    r = np.sqrt(height**2 + width**2) / 2
    centery = (width // 2)-1
    centerx = (height // 2)-1

    alpha = alphaChoice.get()

    n = nChoice.get()#Liczba Emiterow

    l = lChoice.get()#Rozpietosc kątowa
    Usefilter = filterChoice.get()

    Showsteps = stepsChoice.get()
    if Usefilter:
        RMSEListFiltered = createSinogram(image,centerx,centery,height,width,r,Usefilter,Showsteps,n, l, alpha, dicom)
        RMSEChart(RMSEListFiltered,Usefilter)
    else:
        RMSEList = createSinogram(image,centerx,centery,height,width,r,Usefilter,Showsteps,n, l, alpha, dicom)
        RMSEChart(RMSEList,Usefilter)


def loadImage():
    selected_filename = imageChoice.get()
    if selected_filename and selected_filename != "Select an image":
        try:
            full_path = os.path.join("Images", selected_filename)
            image = imread(full_path)
            print(f"Image shape: {image.shape}")
            if len(image.shape) == 3:
                image = rgb2gray(image)
            app(image)
        except Exception as e:
            print("Error loading image:", e)

def loadDicom():
    selected_filename = imageChoiceDicom.get()
    if selected_filename and selected_filename != "Select an image":
        try:
            full_path = os.path.join("ImagesDicom", selected_filename)
            dicom = pydicom.dcmread(full_path)
            image = dicom.pixel_array.astype(float)
            image = (np.maximum(image, 0) / image.max()) * 255.0

            print(f"Image shape: {image.shape}")
            if len(image.shape) == 3:
                image = rgb2gray(image)
            app(image, True)
        except Exception as e:
            print("Error loading image:", e)

def saveDicom(image, filename):
    fileMeta = Dataset()
    fileMeta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    fileMeta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    fileMeta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    ds = FileDataset(None, {}, preamble=b"\0" * 128)
    ds.file_meta = fileMeta

    ds.is_little_endian = True
    ds.is_implicit_VR = False


    name = nameEntryData.get()
    surname = surnameEntryData.get()
    full_name = f"{surname}^{name}"
    age = ageEntryData.get()
    age_dicom = f"{int(age):03d}Y" if age.isdigit() else ""
    gender = genderChoice.get()
    gender_dicom = "M" if gender == "Mężczyzna" else "F" if gender == "Kobieta" else ""
    date = calendar.get_date().replace("-", "")
    date_parts = date.split('/')
    formatted_date = f"20{date_parts[2]}{date_parts[0].zfill(2)}{date_parts[1].zfill(2)}"
    comment = descriptionText.get("1.0", "end").strip()

    ds.SOPClassUID = SecondaryCaptureImageStorage
    ds.SOPInstanceUID = fileMeta.MediaStorageSOPInstanceUID
    ds.PatientName = full_name
    ds.PatientAge = age_dicom
    ds.PatientSex = gender_dicom
    ds.PatientID = "12345"
    ds.ImageComments = comment
    ds.Date = formatted_date
    ds.Modality = "CT"
    ds.SeriesInstanceUID = pydicom.uid.generate_uid()
    ds.StudyInstanceUID = pydicom.uid.generate_uid()
    ds.FrameOfReferenceUID = pydicom.uid.generate_uid()   


    ds.BitsStored = 8
    ds.BitsAllocated = 8
    ds.SamplesPerPixel = 1
    ds.HighBit = 7
    ds.ImagesInAcquisition = 1
    ds.InstanceNumber = 1

    ds.Rows, ds.Columns = image.shape
    ds.ImageType = r"ORIGINAL\PRIMARY\AXIAL"
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.PixelRepresentation = 0

    pydicom.dataset.validate_file_meta(ds.file_meta, enforce_standard=True)
    ds.PixelData = image.tobytes()
    folderPath = "ReconstructedDicoms"
    fullFilePath = os.path.join(folderPath,filename)
    ds.save_as(fullFilePath, write_like_original=False)
    

def readDicomData():
    filePath = filedialog.askopenfilename(
        title="Select DICOM File",
        filetypes=(("DICOM files", "*.dcm"), ("All files", "*.*"))
    )
    patientData = pydicom.dcmread(filePath)
    patientName = patientData.PatientName
    patientAge = patientData.PatientAge
    patientGender = patientData.PatientSex
    patientID = patientData.PatientID
    date = patientData.Date
    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    patientComments = patientData.ImageComments

    print("Informacje o badaniu:")
    print("Data badania: ",formatted_date)
    print("Imie i nazwisko pacjenta: ",patientName)
    print("Wiek pacjenta: ",patientAge)
    print("Płeć pacjenta: ",patientGender)
    print("ID pacjenta: ",patientID)
    print("Komentarz: ",patientComments)
    plt.imshow(patientData.pixel_array,cmap="gray")
    plt.show()
    


def switchToDicom():
    dicomFrame.grid(row=1, column=0, padx=10, pady=10)
    standardFrame.grid_forget()   

def switchToStandard():
    standardFrame.grid(row=1, column=0, padx=10, pady=10)
    dicomFrame.grid_forget()

def showDataEntry():
    dataFrame.grid(row=2, column=10, padx=5,pady=5)

def hideDataEntry():
    dataFrame.grid_forget()

def validateNumberInput(P):
    if P == "" or P.isdigit():
        return True
    return False
def validateStringInput(P):
    if any(char.isdigit() for char in P):
        return False
    return True


root = tk.Tk()
root.title("Symulacja tomografii komputerowej")
root.geometry("1000x900")

modeFrame = tk.Frame(root)
modeFrame.grid(row=0, column=0, pady=10)

tk.Button(modeFrame, text="Tryb klasyczny", command=switchToStandard).grid(row=0, column=0, padx=5)
tk.Button(modeFrame, text="Tryb DICOM", command=switchToDicom).grid(row=0, column=1, padx=5)
tk.Button(modeFrame, text="Odczytaj dane DICOM", command = readDicomData).grid(row=0,column=2,padx=5)

images = ["Kolo.jpg", "Kropka.jpg", "Kwadraty2.jpg", "Paski2.jpg",
        "Shepp_logan.jpg", "CT_ScoutView-large.jpg", "CT_ScoutView.jpg",
        "SADDLE_PE-large.jpg", "SADDLE_PE.jpg"]
imagesDicom = ["Kolo.dcm", "Kropka.dcm", "Kwadraty2.dcm", "Paski2.dcm",
        "Shepp_logan.dcm", "CT_ScoutView-large.dcm", "CT_ScoutView.dcm",
        "SADDLE_PE-large.dcm", "SADDLE_PE.dcm"]

imageChoice = tk.StringVar()
imageChoiceDicom = tk.StringVar()

standardFrame = tk.Frame(root)
standardFrame.grid(row=1, column=0, padx=10, pady=10)

dicomFrame = tk.Frame(root)
dicomFrame.grid(row=2, column=0, padx=10, pady=10)
dicomFrame.grid_forget() 

combo = ttk.Combobox(standardFrame, values = images, textvariable=imageChoice)
combo.set("Images")
combo.grid(row=0, column=0, padx=10, pady=10)

combo = ttk.Combobox(dicomFrame,values = imagesDicom, textvariable=imageChoiceDicom)
combo.set("Dicom Images")
combo.grid(row=0, column=0, padx=10, pady=10)

btn = tk.Button(standardFrame, text="Załaduj obraz", command=loadImage)
btn.grid(row=1, column=0, pady=5)


btnDicom = tk.Button(dicomFrame, text="Załaduj plik DICOM", command=loadDicom)
btnDicom.grid(row=1, column=0, pady=5)

paramsFrame = tk.Frame(root)
paramsFrame.grid(row=3, column=0, pady=10, rowspan=2)

def update_alpha_label(value):
    alpha=float(value)
    ilosc=round(180/alpha,0)
    alphaValueLabel.config(text=f"Ilosc Skanów: {ilosc}")

alphaChoice = tk.DoubleVar()
alphaLabel = tk.Label(paramsFrame, text="Alpha")
alphaLabel.grid(row=0, column=0, padx=10, pady=1)
# alphaSlider = tk.Scale(paramsFrame, variable=alphaChoice,from_=1,to_=10,orient="horizontal")
alphaSlider = tk.Scale(paramsFrame, variable=alphaChoice, from_=0.1, to=2, orient="horizontal", resolution=0.05,command=update_alpha_label,width=20,length=250)
alphaSlider.grid(row=0, column=1, padx=10, pady=1)
alphaValueLabel = tk.Label(paramsFrame, text=f"Ilosc Skanów: {180/alphaChoice.get()}")
alphaValueLabel.grid(row=0, column=2, padx=10)


nChoice = tk.IntVar(value=1)
nLabel = tk.Label(paramsFrame, text="Liczba detektorów")
nLabel.grid(row=1, column=0, padx=10, pady=1)
nSlider = tk.Scale(paramsFrame,variable=nChoice,from_=30,to_=720,orient="horizontal",resolution=5,width=20,length=250)
nSlider.grid(row=1, column=1, padx=10, pady=5)


lChoice = tk.IntVar(value=1)
lLabel = tk.Label(paramsFrame, text="Rozpiętość kątowa")
lLabel.grid(row=2, column=0, padx=10, pady=1)
lSlider = tk.Scale(paramsFrame,variable=lChoice,from_=1,to_=270,orient="horizontal",resolution=1,width=20,length=250)
lSlider.grid(row=2, column=1, padx=10, pady=5)

filterChoice = tk.BooleanVar(value=False)
filterCheckbox = ttk.Checkbutton(paramsFrame, text="Filtr", variable=filterChoice)
filterCheckbox.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

stepsChoice = tk.BooleanVar(value=False)
stepsCheckbox = ttk.Checkbutton(paramsFrame, text="Kroki Pośrednie", variable=stepsChoice)
stepsCheckbox.grid(row=4, column=0, columnspan=2, padx=10, pady=5)

dataButton = tk.Button(dicomFrame, text="Wprowadź dane", command=showDataEntry)
dataButton.grid(row=0, column=2, padx=10, pady=5)

dataFrame = tk.Frame(dicomFrame)
dataFrame.grid(row=4, column=10, padx=5, pady=5)
dataFrame.grid_forget() 

nameLabelData = tk.Label(dataFrame, text="Imię:")
nameLabelData.grid(row=0, column=0, padx=10, pady=5)

vcmdName = (dataFrame.register(validateStringInput), '%P')

nameEntryData = tk.Entry(dataFrame, validate="key",validatecommand=vcmdName)
nameEntryData.grid(row=0, column=1, padx=10, pady=5)

surnameLabelData = tk.Label(dataFrame, text="Nazwisko:")
surnameLabelData.grid(row=1, column=0, padx=10, pady=5)

vcmdSurname = (dataFrame.register(validateStringInput), '%P')

surnameEntryData = tk.Entry(dataFrame, validate="key",validatecommand=vcmdSurname)
surnameEntryData.grid(row=1, column=1, padx=10, pady=5)

ageLabelData = tk.Label(dataFrame, text="Wiek:")
ageLabelData.grid(row=2, column=0, padx=10, pady=5)

vcmdAge = (dataFrame.register(validateNumberInput), '%P')

ageEntryData = tk.Entry(dataFrame, validate="key",validatecommand=vcmdAge)
ageEntryData.grid(row=2, column=1, padx=10, pady=5)

genderChoice = tk.StringVar(value="")
genderChoice.set(None)

genderLabel = tk.Label(dataFrame,text="Płeć:")
genderLabel.grid(row=3,column=0,padx=5)

maleRadio = tk.Radiobutton(dataFrame, text="Mężczyzna", variable=genderChoice, value="Mężczyzna")
maleRadio.grid(row=3, column=1, padx=5, sticky='w')

femaleRadio = tk.Radiobutton(dataFrame, text="Kobieta", variable=genderChoice, value="Kobieta")
femaleRadio.grid(row=3, column=1, padx=5, sticky='e')

calendarLabelData = tk.Label(dataFrame,text = "Data badania:")
calendarLabelData.grid(row=4,column=0,padx=10,pady=5)

today = datetime.today()

calendar = Calendar(dataFrame, selectmode='day', year=today.year, month=today.month, day=today.day)
calendar.grid(row=4,column=1,padx=10,pady=5)

button = tk.Button(dataFrame, text="Wybierz datę")
button.grid(row=5,column=1,padx=10,pady=5)

descriptionLabel = tk.Label(dataFrame, text="Komentarz:")
descriptionLabel.grid(row=5, column=2, padx=10, pady=5)

descriptionText = tk.Text(dataFrame, height=5, width=30)
descriptionText.grid(row=6, column=2, padx=10, pady=5)

root.mainloop()
