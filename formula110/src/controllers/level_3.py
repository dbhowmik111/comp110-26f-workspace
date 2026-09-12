"""__author__: str = "730986400" """

"""Self-driving robotic race car controller demo."""

from racing import RobotCommand, RobotSensors

RACING_NAME: str = "Level 3"
RACING_COLOR: str = "#FEDD00"


def control(sensors: RobotSensors) -> RobotCommand:
    """Steer using camera-based heading error instead of wall sensors."""
    heading_error_degrees: float = sensors.camera.heading_error_degrees
    steer: float = max(-1.0, min(1.0, heading_error_degrees / 45.0))

    throttle: float = (15.0 - sensors.odometry.speed_mps) / 15.0

    return RobotCommand(throttle=throttle, steer=steer)
