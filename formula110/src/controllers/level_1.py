"""__author__: str = "730986400" """

"""Self-driving robotic race car controller demo."""

from racing import RobotCommand, RobotSensors

RACING_NAME: str = "Level 1"
RACING_COLOR: str = "#FEDD00"


def control(sensors: RobotSensors) -> RobotCommand:
    """Go faster while below a maximum speed, then ease off."""
    max_speed_mps: float = 10.0
    throttle: float = 0.0
    steer: float = 0.0

    if sensors.odometry.speed_mps < max_speed_mps:
        throttle = 0.6
    else:
        throttle = 0.1

    if sensors.wall_lidar.front_left_m < 5.0:
        steer = 1.0
    elif sensors.wall_lidar.front_right_m < 5.0:
        steer = -1.0
    else:
        steer = 0.0

    return RobotCommand(throttle=throttle, steer=steer)
