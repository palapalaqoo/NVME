
import matplotlib.pyplot as plt
import numpy as np

x = [1000, 2000, 3000, 4000]
y = [10000, 70000, 30000, 20000]

plt.ion()
fig = plt.figure()

ax = fig.add_subplot(111)
line1, = ax.plot(x, y, 'b-')

fig.canvas.draw()
fig.canvas.draw()
fig.canvas.draw()
fig.canvas.draw()
y = [20000, 80000, 40000, 30000]
line1.set_ydata(y)
fig.canvas.draw()
fig.canvas.draw()
fig.canvas.draw()
y = [30000, 90000, 50000, 40000]
line1.set_ydata(y)
fig.canvas.draw()

for phase in np.linspace(0, 10*np.pi, 100):
    line1.set_ydata(np.sin(0.5 * x + phase))
    fig.canvas.draw()