import numpy as np
import matplotlib.pyplot as plt
import math
from skimage.io import imread
from skimage.color import rgb2gray
from skimage.draw import line_nd
from statistics import mean

# Wczytaj obraz PNG
# image = imread("Kropka.jpg")
image = imread("SADDLE_PE.JPG")



# Konwersja do skali szarości, jeśli obraz jest kolorowy
if len(image.shape) == 3:
    image = rgb2gray(image)


print(image.shape)
# H, W =image.shape
# center = (H//2, W//2)
# R = 

#Zwraca teroetyczny index środka obrazu 
def calculate_center(image):
    H, W = image.shape
    # H = 99
    # W = 99
    if(H%2==1 and W%2==1):
        center = (H//2, W//2)
        return center
    elif(H%2==0 and W%2==0):
        row1 = (H//2)-1
        col1 = (W//2)-1
        row2 = (H//2)-1
        col2 = (W//2)
        row3 = (H//2)
        col3 = (W//2)-1
        row4 = (H//2)
        col4 = (W//2)
        
        rows = np.array([row1,row2,row3,row4])
        cols = np.array([col1,col2,col3,col4])
        return np.mean(rows),np.mean(cols)
    elif(H%2==0 and W%2==1):
        col = (W//2)
        row1 = (H//2)-1
        row2 = (H//2)

        rows = np.array([row1,row2])
        return np.mean(rows),col
    elif(H%2==1 and W%2==0):    
        row = (H//2)
        col1 = (W//2)-1
        col2 = (W//2)

        cols = np.array([col1,col2])
        return row,np.mean(cols)

def calculate_radius(center):

    return math.sqrt((center[0] - 0)**2 + (center[1] - 0)**2)

def circle_points(image, center, radius, num_points = 100):
    cx , cy = center
    angles = np.linspace(0, 2*np.pi, num_points)
    
    x_points = cx + radius * np.cos(angles)
    y_points = cy + radius * np.sin(angles)

    x_points = np.round(x_points).astype(int)
    y_points = np.round(y_points).astype(int)

    return x_points, y_points

# def circle_mask(image, center, radius):
#     H, W = image.shape
#     mask = np.zeros((H, W), dtype=bool)
#     for i in range(H):
#         for j in range(W):
#             if (i-center[0])**2 + (j-center[1])**2 <= radius**2:
#                 mask[i, j] = True
#     return mask

image = np.zeros((100, 100))

center = calculate_center(image)
radius = calculate_radius(center)
x_points, y_points = circle_points(image,center,radius)

valid_mask = (x_points >= 0) & (x_points < 100) & (y_points >= 0) & (y_points < 100)
x_points = x_points[valid_mask]
y_points = y_points[valid_mask]
image[y_points, x_points] = 1  

# for x, y in zip(x_points, y_points):
#     rr, cc = line_nd((center[1], center[0]), (y, x))  # (row, col) format
#     valid_mask = (rr >= 0) & (rr < 100) & (cc >= 0) & (cc < 100)  # Keep in bounds
#     image[rr[valid_mask], cc[valid_mask]] = 1  # Draw lines

plt.imshow(image, cmap='gray')
plt.title("Punkty na okręgu")
plt.axis('off')
plt.show()


##############################################################
############
# scan_1d_values = []
# for i in range(0,np.size(image[0])):
#     start=(0,i)
#     end=(np.size(image[0]),i)
#     rr,cc = line_nd(start,end)
#     Values=image[rr,cc]
#     Intensity=np.sum(Values)
#     scan_1d_values.append(Intensity)

# scan_1d_values = np.array(scan_1d_values)
############

#scan_1d = np.sum(image, axis=0)

# Wyświetlenie oryginalnego obrazu
# plt.figure(figsize=(10, 5))
# plt.subplot(1, 2, 1)
# plt.imshow(image, cmap="gray")
# plt.title("Oryginalny obraz")
# plt.axis("off")

# Wyświetlenie wyniku skanowania 1D
# plt.subplot(1, 2, 2)
# plt.plot(scan_1d_values)
# plt.title("Skan 1D (projekcja pionowa)")
# plt.xlabel("Pozycja detektora")
# plt.ylabel("Suma wartości pikseli")
# plt.show()
