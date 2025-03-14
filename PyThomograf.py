import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.draw import line_nd

image = imread("Kolo.jpg")

if len(image.shape) == 3:
    image = rgb2gray(image)

height, width = image.shape[:2]

r = np.sqrt(height**2 + width**2) / 2

scan_1d_values = []

for j in range(0, 181):
    emitter_scan = []
    for i in range(0, 91):
        start = (r * np.cos(np.radians(i + j)), r * np.sin(np.radians(i + j)))
        end = (r * np.cos(np.radians(i + j)), r * np.sin(np.radians(-1*i + 180 + j)))

        rr, cc = line_nd(start, end)
        rr = np.clip(rr, 0, height - 1)
        cc = np.clip(cc, 0, width - 1)

        Values = image[rr, cc]
        Intensity = np.sum(Values)

        emitter_scan.append(Intensity)

    scan_1d_values.append(emitter_scan)

#scan_1d_values = np.array(scan_1d_values).T  # Transponowanie macierzy

plt.figure(figsize=(10, 5))
plt.imshow(scan_1d_values, cmap='gray', aspect='auto', origin='lower')
plt.title("Sinogram")
plt.xlabel("Pozycja detektora (kąty)")
plt.ylabel("Pozycja detektora (projekcje)")
plt.colorbar(label="Suma wartości pikseli")
plt.show()
