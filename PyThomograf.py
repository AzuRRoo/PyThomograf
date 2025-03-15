import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.draw import line_nd
from skimage.color import gray2rgb
import time

image = imread("Kropka.jpg")

image_empty = np.zeros((image.shape[0],image.shape[1]),dtype=float)


if len(image.shape) == 3:
    image = rgb2gray(image)

height, width = image.shape[:2]
print(f"Obraz: wysokość={height}, szerokość={width}")
print(f"Lewy górny róg: (0, 0)")
print(f"Prawy górny róg: (0, {width-1})")
print(f"Lewy dolny róg: ({height-1}, 0)")
print(f"Prawy dolny róg: ({height-1}, {width-1})")
r = np.sqrt(height**2 + width**2) / 2
centerx = width // 2
centery = height // 2
print(r)

def rekonstruct(image_empty,sinogram):
    for j in range(0, 361):
        for i in range(0, liczbaEm):
            pos = (i - liczbaEm / 2) / 2  # Pozycja emitera
            start = (r * np.cos(np.radians(pos + j)) + centerx,
                     r * np.sin(np.radians(pos + j)) + centery)
            end = (r * (-np.cos(np.radians(-pos + j))) + centerx,
                   r * (-np.sin(np.radians(-pos + j))) + centery)

            # Interpolacja liniowa dla dodania wartości do obrazu
            rr = np.linspace(start[0], end[0], num=width).astype(int)
            cc = np.linspace(start[1], end[1], num=height).astype(int)

            # Ograniczenie do zakresu obrazu
            rr = np.clip(rr, 0, height - 1)
            cc = np.clip(cc, 0, width - 1)

            # Dodanie wartości z sinogramu do obrazu
            image_empty[cc, rr] += sinogram[j][i]  

    return image_empty

        


def filtr(scan_1d_values):
    print(scan_1d_values)

scan_1d_values = []
liczbaEm=181

for j in range(0, 361):
    emitter_scan = []
    image_copy = gray2rgb(image)
    for i in range(0, liczbaEm):
        pos=(i-liczbaEm/2)/2
        start = (r * np.cos(np.radians(pos + j))+centerx, r * np.sin(np.radians(pos + j))+centery)
        end = (r * (-1*np.cos(np.radians(-pos +j)))+centerx,r * (-1*np.sin(np.radians(-pos + j)))+centery)
        rr, cc = line_nd(start, end)
        #print(start,end)
        rr = np.clip(rr, 0, height - 1)
        cc = np.clip(cc, 0, width - 1)

        Values = image[rr, cc]
        Intensity = np.sum(Values)

        emitter_scan.append(Intensity)
        if(pos==0):
            image_copy[rr, cc] = [0, 255, 0]
        else:
            image_copy[rr, cc] = [255,255,255]


    #Rysujemy linię na kopii obrazu
      # Zmieniamy wartość pikseli linii na biały (dla obrazów w skali szarości)

    #Wyświetlamy obraz z aktualną linią
    plt.imshow(image_copy, cmap="gray")
    plt.title(f"Linia dla j={j}")
    plt.axis("off")
    plt.pause(0.0001)  # Krótka pauza, aby zobaczyć zmianę
    plt.clf()
    scan_1d_values.append(emitter_scan)

image = rekonstruct(image_empty, scan_1d_values)
plt.imshow(image, cmap="gray")

plt.figure(figsize=(10, 5))
plt.imshow(scan_1d_values, cmap='gray', aspect='auto', origin='lower')
plt.title("Sinogram")
plt.xlabel("Pozycja detektora (kąty)")
plt.ylabel("Pozycja detektora (projekcje)")
plt.colorbar(label="Suma wartości pikseli")
plt.show()
