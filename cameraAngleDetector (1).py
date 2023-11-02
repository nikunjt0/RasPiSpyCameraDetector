import pandas as pd
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

# Load IMU data
imu_data = pd.read_csv('/home/pi/Documents/lab3/postlab/stepdata15:04:14.csv')

# Load RSSI data
rssi_data = pd.read_csv('/home/pi/Documents/lab3/postlab/part3Data.csv15:04:14-edited.csv')

# Assuming 'time' is in the HH:MM:SS:ff format, convert it to a datetime object
imu_data['time'] = pd.to_datetime(imu_data['time'], format='%H:%M:%S.%f')

# Find peaks in the Z-axis data (adjust parameters as needed)
peaks, _ = find_peaks(imu_data['z'], height=1.2, distance=5)

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
plt.xlim(-2, 3)
plt.ylim(0, 12)

# Calculate the point density
density = np.zeros(len(rssi_data))

for i in range(len(rssi_data)):
    x, y = rssi_data['x'].values[i], rssi_data['y'].values[i]
    density[i] = np.sum((rssi_data['x'] - x)**2 + (rssi_data['y'] - y)**2 < 0.5**2)  # Adjust the radius as needed

# Determine the indices of the regions with the highest point densities for the top half
top_density_indices = np.argpartition(density, -len(density)//2)[-len(density)//2:]

# Calculate the coordinates of the big box that encompasses these regions
min_x = rssi_data['x'].values[top_density_indices].min() - 0.5
max_x = rssi_data['x'].values[top_density_indices].max() + 0.5
min_y = rssi_data['y'].values[top_density_indices].min() - 0.5
max_y = rssi_data['y'].values[top_density_indices].max() + 0.5

# Calculate the center of the region with the top half of the highest point densities
location_x = (min_x + max_x) / 2
location_y = (min_y + max_y) / 2

# Create a single big box around the areas with the top half of the highest point densities
plt.gca().add_patch(plt.Rectangle((min_x, min_y), max_x - min_x, max_y - min_y, linewidth=2, edgecolor='red', facecolor='none'))

# Create a grid for interpolation within the region of interest
x_grid = np.linspace(min_x, max_x, 100)
y_grid = np.linspace(min_y, max_y, 100)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)

# Interpolate RSSI values over the grid within the region of interest
interpolated_rssi = griddata((rssi_data['x'], rssi_data['y']), rssi_data['rssi'], (x_mesh, y_mesh), method='cubic')

# Find the location with the highest interpolated RSSI value within the region of interest
max_rssi_index = np.unravel_index(np.nanargmax(interpolated_rssi), interpolated_rssi.shape)
max_rssi_x = x_grid[max_rssi_index[1]]
max_rssi_y = y_grid[max_rssi_index[0]]

# Calculate the angle from the highest expected RSSI to the point of highest density
angle = np.degrees(np.arctan2(location_y - max_rssi_y, location_x - max_rssi_x))

# Plot the location with the highest expected RSSI value
plt.scatter(max_rssi_x, max_rssi_y, c='red', marker='o', s=100, label='Highest Expected RSSI')
plt.text(max_rssi_x, max_rssi_y, f'Highest Expected RSSI', fontsize=12, color='red')

# Add an arrow indicating the direction from highest expected RSSI to the point of highest density
plt.arrow(max_rssi_x, max_rssi_y, location_x - max_rssi_x, location_y - max_rssi_y, head_width=0.2, head_length=0.2, fc='red', ec='red')

# Iterate through each point in rssi_data to draw arrows towards the point of highest density
for index, row in rssi_data.iterrows():
    x = row['x']
    y = row['y']

    # Check if the point is inside the red box
    if x >= min_x and x <= max_x and y >= min_y and y <= max_y:
        continue  # Skip drawing arrows inside the red box

    # Add an arrow indicating the direction toward the point of highest density
    plt.arrow(x, y, (location_x - x) * 0.1, (location_y - y) * 0.1, head_width=0.2, head_length=0.2, fc='blue', ec='blue')

plt.legend()
plt.show()