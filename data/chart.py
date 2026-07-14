import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import ConciseDateFormatter
import numpy as np
from datetime import datetime

df = pd.read_csv("day_2_data.csv")

x = df['recieved_time'].values
x = x.tolist()
x = [datetime.fromisoformat(t) for t in x]
hz_110 = df['hz_110_dbfs'].values
hz_440 = df['hz_440_dbfs'].values
hZ_1000 = df['hz_1000_dbfs'].values
hz_4000 = df['hz_4000_dbfs'].values


fig, ax = plt.subplots()

# ax.plot(x, hz_110, label = "60-160 Hz", color="#847996", alpha = 0.8, linewidth=1)
# ax.plot(x, hz_440, label = "390-490 Hz", color = "#88B7B5", alpha = 0.8, linewidth=1)
# ax.plot(x, hZ_1000, label = "950-1050 Hz", color = "#A7CAB1", alpha = 0.8, linewidth=1)

alpha = 0.6
s = 3
ax.scatter(x, hz_110, label = "60-160 Hz", color="#847996", alpha = alpha, s=s)
ax.scatter(x, hz_440, label = "390-490 Hz", color = "#88B7B5", alpha = alpha, s=s)
ax.scatter(x, hZ_1000, label = "950-1050 Hz", color = "#548C64", alpha = alpha, s=s)


# Data is noisy around 4000 Hz
# ax.plot(x, hz_4000, label = "3950-4050 Hz", color = "#310A31", alpha = 0.8, linestyle='--', linewidth=1)

ax.xaxis.set_major_formatter(ConciseDateFormatter(ax.xaxis.get_major_locator()))
# ax.yaxis()

ax.set_title("Audio Measurements Over Time (Backyard Test)")
ax.set_xlabel('Time Received')
ax.set_ylabel('dBFS')
ax.legend()

plt.savefig("day_2_test.png")