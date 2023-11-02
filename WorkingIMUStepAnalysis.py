import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

#14:11 is part 1
#15:04 is part 2
#15:25 is part 2 EC


# Load IMU data
imu_data = pd.read_csv('/home/pi/Documents/lab3/postlab/stepdata15:25:25.csv')

# Load RSSI data
rssi_data = pd.read_csv('/home/pi/Documents/lab3/postlab/part3Data.csv15:25:25.csv')

# Assuming 'time' is in the HH:MM:SS:ff format, convert it to a datetime object
imu_data['time'] = pd.to_datetime(imu_data['time'], format='%H:%M:%S.%f')

# Find peaks in the Z-axis data (adjust parameters as needed)
peaks, _ = find_peaks(imu_data['z'], height=1.2, distance=5)

# Plot the Z-axis data with detected peaks
plt.plot(imu_data['time'].to_numpy(), imu_data['z'].to_numpy())
plt.plot(imu_data['time'][peaks].to_numpy(), imu_data['z'][peaks].to_numpy(), 'ro')  # Highlight peaks
plt.xlabel('Time')
plt.ylabel('Z-axis Data')
plt.title('IMU Data with Detected Peaks')
plt.show()


print(peaks)

step_size = 0.6  # Known step size in meters
x, y = 0, 0  # Initialize starting position (assumes the user starts at the origin)
path_data = []  # List to store (x, y, time) data

for peak_index in peaks:
    direction = imu_data.at[peak_index, 'direction']
    time = imu_data.at[peak_index, 'time']

    # Update (x, y) coordinates based on the direction and step size
    if direction == 0:  # Walking in the +y direction
        y += step_size
    elif direction == 1:  # Walking in the +x direction
        x += step_size
    elif direction == 2:  # Walking in the -y direction
        y -= step_size
    elif direction == 3:  # Walking in the -x direction
        x -= step_size

    path_data.append((x, y, time))

# Create a DataFrame with columns 'x', 'y', and 'time'
path_df = pd.DataFrame(path_data, columns=['x', 'y', 'time'])

# Assume the original path_df contains (x, y) coordinates and 'time' column
# Create an empty DataFrame to store the new points
new_points = pd.DataFrame(columns=['x', 'y', 'time'])

# Iterate through the original path_df to calculate new points
for i in range(len(path_df) - 1):
    point1 = path_df.iloc[i]
    point2 = path_df.iloc[i + 1]
    
    # Calculate the time difference and step size for inserting new points
    time_diff = (point2['time'] - point1['time']).total_seconds()
    step_size = time_diff / 10  # Insert 6 points, including the existing points
    
    for j in range(10):
        # Calculate the new time for each point
        new_time = point1['time'] + pd.Timedelta(seconds=j * step_size)
        
        # Interpolate (x, y) coordinates based on a constant rate of speed
        x_interpolated = point1['x'] + (point2['x'] - point1['x']) / 10 * j
        y_interpolated = point1['y'] + (point2['y'] - point1['y']) / 10 * j
        
        new_points = pd.concat([new_points, pd.DataFrame({'x': [x_interpolated], 'y': [y_interpolated], 'time': [new_time]})], ignore_index=True)

# Concatenate the original path_df with the new_points
path_df = pd.concat([path_df, new_points]).sort_values(by='time').reset_index(drop=True)

# Now, path_df contains the original (x, y) points along with the interpolated points


rssi_data['time'] = pd.to_datetime(rssi_data['time'], format='%H:%M:%S.%f')

# Create lists to store the matched (x, y) coordinates for RSSI data
matched_x = []
matched_y = []

# Iterate through RSSI data
for index, row in rssi_data.iterrows():
    rssi_time = row['time']
    # Find the nearest (x, y) point to the RSSI time
    nearest_point = path_df.iloc[(path_df['time'] - rssi_time).abs().idxmin()]
    matched_x.append(nearest_point['x'])
    matched_y.append(nearest_point['y'])

# Add the matched (x, y) coordinates to the RSSI DataFrame
rssi_data['x'] = matched_x
rssi_data['y'] = matched_y

# Create a scatterplot of RSSI values at (x, y) points
plt.figure(figsize=(10, 6))
plt.scatter(rssi_data['x'], rssi_data['y'], c=rssi_data['rssi'], cmap='viridis', s=50)
plt.colorbar(label='RSSI Data')
plt.title('RSSI Data at Nearest (x, y) Points')
plt.xlabel('X-coordinate')
plt.ylabel('Y-coordinate')
plt.show()



# Create a DataFrame with only 'x', 'y', and 'rssi' columns from rssi_data
interpolation_data = rssi_data[['x', 'y', 'rssi']]

# Create a grid of points for interpolation
x_grid = np.linspace(path_df['x'].min(), path_df['x'].max(), 10)  # Adjust the number of points as needed
y_grid = np.linspace(path_df['y'].min(), path_df['y'].max(), 10)  # Adjust the number of points as needed
x_grid, y_grid = np.meshgrid(x_grid, y_grid)

# Perform 2D interpolation using the 'interpolation_data'
rssi_grid = griddata((interpolation_data['x'], interpolation_data['y']), interpolation_data['rssi'], (x_grid, y_grid), method='cubic')

# Create a contour plot of the estimated RSSI values
plt.figure(figsize=(10, 6))
plt.contourf(x_grid, y_grid, rssi_grid, cmap='viridis', levels=10)  # Adjust 'levels' as needed
plt.colorbar(label='Estimated RSSI')
plt.scatter(rssi_data['x'], rssi_data['y'], c=rssi_data['rssi'], cmap='viridis', s=50, edgecolor='k', label='Measured RSSI')
plt.xlabel('X-coordinate')
plt.ylabel('Y-coordinate')
plt.title('Estimated RSSI Map')
plt.legend()
plt.show()