"""Self-driving robotic race car controller demo."""

from racing import RobotCommand, RobotSensors

RACING_NAME: str = "Crash Dummy"
RACING_COLOR: str = "#FEDD00"


def control(sensors: RobotSensors) -> RobotCommand:
    """This demo is all gas, no steering."""
    return RobotCommand(throttle=1.0, steer=0.0)
