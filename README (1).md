
# CS 437 Midterm Report (Nikunj Tyagi and Avery Plote)

To run the programs as intended:

Step 1: Use accurate_distance_vs_rssi_imu.py to find as many RSSI packets in a room for one minute. Make sure to use the joystick every time you take a turn, face the raspberry pi in the same direction, and exagerrate movement in the z-direction as you take a step.

Step 2: Find the csv files of your intended run. One should be named stepdata and the other should be named part3Data, but both of them must refer to the same timestamp.

Step 3: Put these in WorkingIMUStepAnalysis.py in the lines for imu_data and rssi_data initialization. The csv file titled stepdata should go into imu_data, and the part3Data should go into rssi_data. Run the code to find the step analysis, path, and interpolated RSSI based on the path

Step 4: Put the same csv files into cameraAngleDetector.py, and run it. This should show you the angle that the camera should be facing.

Step 5: Use all previous graphs and readings to make estimated guess on location of camera

Let us know if you have any questions at nikunjt2@illinois.edu or averycp2@illinois.edu

Thanks!