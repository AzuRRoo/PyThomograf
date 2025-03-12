#test
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.draw import line_nd

# Wczytaj obraz PNG
image = imread("Kropka.jpg")

# Konwersja do skali szarości, jeśli obraz jest kolorowy
if len(image.shape) == 3:
    image = rgb2gray(image)

scan_1d_values = []
for i in range(0,np.size(image[0])):
    start=(0,i)
    end=(np.size(image[0]),i)
    rr,cc = line_nd(start,end)
    Values=image[rr,cc]
    Intensity=np.sum(Values)
    scan_1d_values.append(Intensity)

scan_1d_values = np.array(scan_1d_values)

#scan_1d = np.sum(image, axis=0)

# Wyświetlenie oryginalnego obrazu
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.imshow(image, cmap="gray")
plt.title("Oryginalny obraz")
plt.axis("off")

# Wyświetlenie wyniku skanowania 1D
plt.subplot(1, 2, 2)
plt.plot(scan_1d_values)
plt.title("Skan 1D (projekcja pionowa)")
plt.xlabel("Pozycja detektora")
plt.ylabel("Suma wartości pikseli")
plt.show()
