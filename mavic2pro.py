#this is the code for DRONE control (MAVIC2PRO)
from controller import Robot, Camera, Compass, GPS, Gyro, InertialUnit, Keyboard, LED, Motor
import os
import time

def clamp(value, low, high):
    return max(low, min(value, high))

def main():
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    # Ensure the save directory exists
    save_directory = "C:\\Users\\ADMIN\\Pictures\\mavic2pro"
    if not os.path.exists(save_directory):
        os.makedirs(save_directory)

    # Get and enable devices
    camera = robot.getDevice("camera")
    camera.enable(timestep)
    
    front_left_led = robot.getDevice("front left led")
    front_right_led = robot.getDevice("front right led")
    imu = robot.getDevice("inertial unit")
    imu.enable(timestep)
    gps = robot.getDevice("gps")
    gps.enable(timestep)
    compass = robot.getDevice("compass")
    compass.enable(timestep)
    gyro = robot.getDevice("gyro")
    gyro.enable(timestep)
    keyboard = Keyboard()
    keyboard.enable(timestep)

    camera_roll_motor = robot.getDevice("camera roll")
    camera_pitch_motor = robot.getDevice("camera pitch")

    # Propeller motors
    motors = {
        "front_left": robot.getDevice("front left propeller"),
        "front_right": robot.getDevice("front right propeller"),
        "rear_left": robot.getDevice("rear left propeller"),
        "rear_right": robot.getDevice("rear right propeller")
    }
    
    for motor in motors.values():
        motor.setPosition(float('inf'))
        motor.setVelocity(1.0)

    print("Start the drone...")
    while robot.step(timestep) != -1:
        if robot.getTime() > 1.0:
            break
    
    print("You can control the drone with your keyboard:")
    print("- 'up': move forward.")
    print("- 'down': move backward.")
    print("- 'right': turn right.")
    print("- 'left': turn left.")
    print("- 'shift + up': increase the target altitude.")
    print("- 'shift + down': decrease the target altitude.")
    print("- 'shift + right': strafe right.")
    print("- 'shift + left': strafe left.")
    print("- 'p': take a picture.")

    # PID Constants
    k_vertical_thrust = 68.5
    k_vertical_offset = 0.6
    k_vertical_p = 3.0
    k_roll_p = 50.0
    k_pitch_p = 30.0
    
    target_altitude = 1.0
    
    while robot.step(timestep) != -1:
        time_now = robot.getTime()
        roll, pitch, _ = imu.getRollPitchYaw()
        altitude = gps.getValues()[2]
        roll_velocity, pitch_velocity, _ = gyro.getValues()
        
        led_state = int(time_now) % 2
        front_left_led.set(led_state)
        front_right_led.set(1 - led_state)
        
        camera_roll_motor.setPosition(-0.115 * roll_velocity)
        camera_pitch_motor.setPosition(-0.1 * pitch_velocity)
        
        roll_disturbance, pitch_disturbance, yaw_disturbance = 0.0, 0.0, 0.0
        key = keyboard.getKey()
        while key > 0:
            if key == Keyboard.UP:
                pitch_disturbance = -2.0
            elif key == Keyboard.DOWN:
                pitch_disturbance = 2.0
            elif key == Keyboard.RIGHT:
                yaw_disturbance = -1.3
            elif key == Keyboard.LEFT:
                yaw_disturbance = 1.3
            elif key == (Keyboard.SHIFT + Keyboard.RIGHT):
                roll_disturbance = -1.0
            elif key == (Keyboard.SHIFT + Keyboard.LEFT):
                roll_disturbance = 1.0
            elif key == (Keyboard.SHIFT + Keyboard.UP):
                target_altitude += 0.05
                print(f"Target altitude: {target_altitude} m")
            elif key == (Keyboard.SHIFT + Keyboard.DOWN):
                target_altitude -= 0.05
                print(f"Target altitude: {target_altitude} m")
            elif key == ord('P') or key == ord('p'):  # Press 'P' to take a picture
                filename = f"{save_directory}\\drone_picture_{int(time.time())}.jpg"
                camera.saveImage(filename, 100)
                print(f"Picture saved as {filename}")
            key = keyboard.getKey()

        roll_input = k_roll_p * clamp(roll, -1.0, 1.0) + roll_velocity + roll_disturbance
        pitch_input = k_pitch_p * clamp(pitch, -1.0, 1.0) + pitch_velocity + pitch_disturbance
        clamped_difference_altitude = clamp(target_altitude - altitude + k_vertical_offset, -1.0, 1.0)
        vertical_input = k_vertical_p * (clamped_difference_altitude ** 3)

        inputs = {
            "front_left": k_vertical_thrust + vertical_input - roll_input + pitch_input - yaw_disturbance,
            "front_right": k_vertical_thrust + vertical_input + roll_input + pitch_input + yaw_disturbance,
            "rear_left": k_vertical_thrust + vertical_input - roll_input - pitch_input + yaw_disturbance,
            "rear_right": k_vertical_thrust + vertical_input + roll_input - pitch_input - yaw_disturbance
        }
        
        motors["front_left"].setVelocity(inputs["front_left"])
        motors["front_right"].setVelocity(-inputs["front_right"])
        motors["rear_left"].setVelocity(-inputs["rear_left"])
        motors["rear_right"].setVelocity(inputs["rear_right"])
    
    robot.cleanup()

if __name__ == "__main__":
    main()
