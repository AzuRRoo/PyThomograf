import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.draw import line_nd
from skimage.color import gray2rgb
import time
import copy
import math
from skimage.transform import radon, iradon
from scipy.fft import fft, ifft, fftfreq

#KWADRATY
# image = imread("Kolo.jpg")# ✅  
# image = imread("Kropka.jpg")# ✅
# image = imread("Kwadraty2.jpg")#✅
image = imread("Paski2.jpg")#❌ #Caly czarny obraz
# image = imread("Shepp_logan.jpg")#✅
#PROSTOKATY
# image = imread("cos.jpg") #❌ -> widac kulke jednakze nie ma  bialego paska
# image = imread("CT_ScoutView-large.jpg")#✅
# image = imread("CT_ScoutView.jpg")#✅

# image = imread("SADDLE_PE-large.jpg")#✅ Nieco wyblakle
# image = imread("SADDLE_PE.jpg")#❌ -> caly czarny obraz



image_shape0 = image.shape[0]
image_shape1 = image.shape[1]

if len(image.shape) == 3:
    image = rgb2gray(image)
print("DUPA: ",image.shape)
height,width = image.shape[:2]
print(f"Obraz: wysokość={height}, szerokość={width}")
print(f"Lewy górny róg: (0, 0)")
print(f"Prawy górny róg: (0, {width-1})")
print(f"Lewy dolny róg: ({height-1}, 0)")
print(f"Prawy dolny róg: ({height-1}, {width-1})")
r = np.sqrt(height**2 + width**2) / 2
centery = (width // 2)-1
centerx = (height // 2)-1
print(r)


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



#Musi dodac padding taki aby zamiast miec
#Kolo z dedtektorami opisane na kwadracie aby bylo jakby wpisane w kwadrat wiekszy

def addPadding(image):
    #Obraz musi byc otoczony przez obwodke szeroka i wyskoa na dwa r minus jego aktualny wymiar
    
    # max_dim = max(image.shape[0],image.shape[1])
    #result to obraz o wymiarach 2*r x 2*r
    result = np.zeros((2*int(r),2*int(r)),dtype=image.dtype)
    print("result shape: ",result.shape)
    #Teraz w sam srodek result musze wrzucic image
    x,y = (image.shape[0])//2,(image.shape[1])//2
    print("x,y: ",x,y)
    print("image shape: ",image.shape)
    z = x+image.shape[0]
    z2 = y+image.shape[1]
    print("z,z2: ",z,z2)
    result[int(r)-x:r-x+image.shape[0],r-y:y+image.shape[1]] = image
    
    return result
# image2 = np.array([
#     [1,2,3],
#     [4,5,6]
# ])
# centered_image_w_padding = addPadding(image2)
# print(centered_image_w_padding)
def makeSquare():
    return np.zeros((2*int(r),2*int(r)))
# addPadding(image)



# image = makeSquare()

def rekonstruct(image_empty, sinogram, alfa, liczbaEm, r, centerx, centery):
    """
    Rekonstruuje obraz na podstawie sinogramu metodą backprojection.
    
    Parametry:
    image_empty - pusty obraz (tablica o zadanych wymiarach)
    sinogram - sinogram jako macierz 2D (wymiary: [liczba_kątów, liczba_detektorów])
    alfa - kąt między kolejnymi projekcjami (w stopniach, zazwyczaj 1)
    liczbaEm - liczba detektorów/emiterów (np. 181)
    r - promień (odległość emiterów/detektorów od środka obrazu)
    centerx, centery - współrzędne środka obrazu
    
    Zwraca:
    Zrekonstruowany obraz (normalizowany do 0-255, typu uint8).
    """ 
    filtered_sinogram = []
    for projection in sinogram:
        filtered_projection = filtr(projection)
        filtered_sinogram.append(filtered_projection)
    plt.figure(figsize=(10, 5))
    plt.imshow(filtered_sinogram, cmap='gray')
    plt.title("Sinogram")
    plt.xlabel("Pozycja detektora (kąty)")
    plt.ylabel("Pozycja detektora (projekcje)")
    plt.colorbar(label="Suma wartości pikseli")
    plt.show()
    filtered_sinogram = np.array(filtered_sinogram)
    num_angles = filtered_sinogram.shape[0]   # liczba kątów (np. 181)
    
    for j in range(num_angles):
        angle = j  # przy alfa=1, kąt = j stopni
        for i in range(liczbaEm):
            # Obliczanie pozycji sensora
            pos = (i - liczbaEm / 2) / 2
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
            image_empty[rr, cc] += filtered_sinogram[j, i]
    
    # Normalizacja zrekonstruowanego obrazu do zakresu 0-255
    image_empty -= np.min(image_empty)
    if np.max(image_empty) != 0:
        image_empty /= np.max(image_empty)
    image_empty *= 255
    
    return image_empty.astype(np.uint8)

def ram_lak_filter(projection):
    n = len(projection)
    
    # Apply FFT
    proj_fft = fft(projection)
    freqs = fftfreq(n)

    # Create Ram-Lak filter in freq domain
    filter_kernel = np.abs(freqs)

    # Apply filter in frequency domain
    filtered_fft = proj_fft * filter_kernel

    # Inverse FFT to get filtered projection
    filtered_projection = np.real(ifft(filtered_fft))
    
    return filtered_projection
        
def filtr(sinogram):
    hardcoded = len(sinogram)#do poprawy edycji 
    mask = []
    for k in range(-hardcoded//2,hardcoded//2 +1):
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

    # filtered = np.zeros(len(sinogram))
    filtered = np.convolve(sinogram, mask, mode='same')
    return filtered


scan_1d_values = []
liczbaEm=181
deep=copy.deepcopy(image)
print(centerx,centery)
for j in range(0, 181):
    emitter_scan = []
    image_copy = gray2rgb(deep)
    for i in range(0, liczbaEm):
        pos=(i-liczbaEm/2)/2
        # print("Pozycja detektora: ",pos)
        start = (r * np.cos(np.radians(pos + j))+centerx, r * np.sin(np.radians(pos + j))+centery)
        end = (r * (-1*np.cos(np.radians(-pos +j)))+centerx,r * (-1*np.sin(np.radians(-pos + j)))+centery)
        rr, cc = Bresenham(int(start[0]), int(start[1]), int(end[0]), int(end[1]))
        rr = np.clip(rr, 0, height - 1)
        cc = np.clip(cc, 0, width - 1)

        Values = image[rr,cc]
        Intensity = np.sum(Values)

        emitter_scan.append(Intensity)



        image_copy[centerx,centery]=[int(255),0,0]
        for test in range(-5,5):
            image_copy[centerx+test,centery]=[int(255),0,0]
            image_copy[centerx+test,centery+test]=[int(255),0,0]
            image_copy[centerx,centery+test]=[int(255),0,0]
        if(pos==0):
            image_copy[rr, cc] = [0, 255, 0]
        else:
            image_copy[rr, cc] = [255,255,255]


    plt.imshow(image_copy)
    plt.title(f"Linia dla j={j}")
    plt.axis("off")
    plt.pause(0.0001)
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
copy2 = rekonstruct(image_empty, np.array(scan_1d_values), 1,180,r,centerx,centery)

# plt.figure(figsize=(8, 8))

plt.imshow(copy2,cmap="gray")
plt.colorbar()
plt.show()