import matplotlib.pyplot as plt
import numpy as np
from math import *

def taylor_cos(xpoints):
    result = []
    for x in xpoints:
        result.append(1 - (x ** 2)/(factorial(2)) + (x ** 4)/(factorial(4)) - (x ** 6)/(factorial(6)))
    return result

def euler_cos(step_size=1/1000):    
    xpoints = []
    ypoints = []

    y = 1
    dy = 0
    t = 0
    end_t = 0.5*pi

    while t < end_t:
        xpoints.append(t)
        ypoints.append(y)
        ddy = -y
        y += dy*step_size + 0.5*ddy*step_size*step_size
        dy += ddy*step_size
        t += step_size

    return xpoints, ypoints

xpoints1, euler_ypoints1 = euler_cos(1/100)  
xpoints2, euler_ypoints2 = euler_cos(1/1000)  
xpoints3, euler_ypoints3 = euler_cos(1/10000)  
xpoints4, euler_ypoints4 = euler_cos(1/100000)  

cos_ypoints1 = np.cos(xpoints1)
cos_ypoints2 = np.cos(xpoints2)
cos_ypoints3 = np.cos(xpoints3)
cos_ypoints4 = np.cos(xpoints4)
taylor_ypoints = taylor_cos(xpoints1)

fig1, ax1 = plt.subplots()
ax1.plot(xpoints1, cos_ypoints1-euler_ypoints1, label="Euler(0.01)")
ax1.plot(xpoints2, cos_ypoints2-euler_ypoints2, label="Euler(0.001)")
ax1.plot(xpoints3, cos_ypoints3-euler_ypoints3, label="Euler(0.0001)")
ax1.plot(xpoints4, cos_ypoints4-euler_ypoints4, label="Euler(0.00001)")
ax1.plot(xpoints1, cos_ypoints1-taylor_ypoints, label="Taylor")
ax1.legend()
# ax1[1].plot(xpoints, euler_ypoints, label="Euler")
# ax1[1].plot(xpoints, taylor_ypoints, label="Taylor")
# ax1[1].legend()

plt.show()