"""__author__: str = "730986400" """

"""Self-driving robotic race car controller demo."""

from racing import RobotCommand, RobotSensors

RACING_NAME: str = "Level 2"
RACING_COLOR: str = "#FEDD00"


def control(sensors: RobotSensors) -> RobotCommand:
    """Scale throttle continuously with speed instead of switching abruptly."""
    throttle: float = (15.0 - sensors.odometry.speed_mps) / 15.0
    steer: float = 0.0

    if sensors.wall_lidar.front_left_m < 6.0:
        steer = 1.0
    elif sensors.wall_lidar.front_right_m < 6.0:
        steer = -1.0
    else:
        steer = 0.0

    return RobotCommand(throttle=throttle, steer=steer)
