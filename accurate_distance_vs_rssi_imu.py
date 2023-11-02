import csv
from datetime import datetime
from scapy.all import *
import time
from sense_hat import SenseHat
from threading import Thread

"""
Run monitor_mode.sh first to set up the network adapter to monitor mode and to
set the interface to the right channel.
To get RSSI values, we need the MAC Address of the connection 
of the device sending the packets.
"""
sense=SenseHat()
path="/home/pi/Documents/lab3/postlab/part3Data.csv"
# Variables to be modified
dev_mac = "e4:5f:01:d4:9f:f9"  # Assigned transmitter MAC
iface_n = "wlan1"  # Interface for network adapter
duration = 60  # Number of seconds to sniff for
timestamp_fname=datetime.now().strftime("%H:%M:%S")
sense.set_imu_config(False,True,False) ## Config the Gyroscope, Accelerometer, Magnetometer
filename=path+timestamp_fname+".csv"
filename2 = "/home/pi/Documents/lab3/postlab/stepdata" + timestamp_fname + ".csv"
step_size = 0.7 # meters
direction = 0

led_timer = time.time()


def create_rssi_file():
    """Create and prepare a file for RSSI values"""
    header = ["date", "time", "dest", "src", "rssi"]
    header2 = ["date", "time", "z", "direction"]
    with open(filename, "w", encoding="UTF8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
    with open(filename2, "w", encoding="UTF8") as f:
         writer = csv.writer(f)
         writer.writerow(header2)


def captured_packet_callback(pkt):
    """Save MAC addresses, time, and RSSI values to CSV file if MAC address of src matches"""
    global led_timer
    missed_count = 0  # Number of missed packets while attempting to write to file
    cur_dict = {}
    # accel=sense.get_accelerometer_raw()  ## returns float values representing acceleration intensity in Gs
    #gyro=sense.get_gyroscope_raw()  ## returns float values representing rotational intensity of the axis in radians per second
    #mag=sense.get_compass_raw()  ## returns float values representing magnetic intensity of the ais in microTeslas

    try:
        cur_dict["mac_1"] = pkt.addr1
        cur_dict["mac_2"] = pkt.addr2
        cur_dict["rssi"] = pkt.dBm_AntSignal
    except AttributeError:
        return  # Packet formatting error

    date_time = datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f").split(",") #Get current date and time
    date = date_time[0]
    csv_time = date_time[1]
    
    if time.time() - led_timer > 3:
         sense.clear()
         led_timer = time.time()

    ################### Your code here ###################

    # Only write the RSSI values of packets that are coming from your assigned transmitter (hint: filter by pkt.addr2, the destination MAC field)
    # Use the 'writerow' method to write the RSSI value and the current timestamp to the CSV file

    ######################################################
    if cur_dict["mac_2"] == dev_mac:
        with open(filename, "a", encoding="UTF8") as f:
            rssi = cur_dict["rssi"]
            #x=accel['x']
            #y=accel['y']
            writer = csv.writer(f)
            writer.writerow([date, csv_time, cur_dict["mac_1"], cur_dict["mac_2"], rssi])
            
            print (rssi, direction)
            #LED matrix stuff
            if (rssi <= 0 and rssi > -20):
                X = [255, 0, 0]  # Red'
                
            if (rssi <= -20 and rssi > -25):
                X = [255, 165, 0]  # orange'           

            if (rssi <= -25 and rssi > -30):
                X = [255, 255, 0]  # Yellow
                
            if (rssi <= -30 and rssi > -35):
                X = [0, 255, 0]  # Green

            if (rssi <= -35 and rssi > -40):
                X = [0, 0, 255] # blue
    
            if (rssi <= -40 and rssi > -50):
                X = [128, 0, 128]  # Purple
                
            if (rssi <= -50 and rssi > -100):
                X = [255, 255, 255] # White


                
            half_and_half = [
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X,
            X, X, X, X, X, X, X, X
            ]
            
            sense.set_pixels(half_and_half)
            
            led_timer = time.time()
            
            

# for reference, "right" on the joystick is towards the USB ports
# 0 = Up (RPi right), 1 = Right, 2 = Down, 3 = Left
def pushed_up(event):
    global direction
    direction = 3
    #direction = (direction + 3) % 4

def pushed_down(event):
    global direction
    direction = 1
    #direction = (direction + 1) % 4

def pushed_left(event):
    global direction
    direction = 2
    #direction = (direction + 2) % 4 
    
def pushed_right(event):
    global direction
    direction = 0
    
    
def imu_data_collector(filename2):
    global direction
    with open(filename2, "a", encoding="UTF8") as f:
        writer = csv.writer(f)
        while True:
            accel = sense.get_accelerometer_raw()
            z = accel['z']
            date_time = datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f").split(",")
            date = date_time[0]
            csv_time = date_time[1]
            writer.writerow([date, csv_time, z, direction])
            time.sleep(0.1)  # Adjust the sleep duration as needed

if __name__ == "__main__":
    create_rssi_file()
    sense.stick.direction_up = pushed_up
    sense.stick.direction_down = pushed_down
    sense.stick.direction_left = pushed_left
    sense.stick.direction_right = pushed_right
    
    # Start the IMU data collection thread
    imu_thread = Thread(target=imu_data_collector, args=(filename2,))
    imu_thread.daemon = True
    imu_thread.start()

    t = AsyncSniffer(iface=iface_n, prn=captured_packet_callback, store=0)
    t.daemon = True
    t.start()
    
    start_date_time = datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f") #Get current date and time

    time.sleep(duration)
    t.stop()
    sense.clear()
    
    print("RSSI data retrival finished")
    
    time.sleep(20)

    print("Start Time: ", start_date_time)