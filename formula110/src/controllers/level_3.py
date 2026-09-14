"""Steer using camera-based lookahead and heading error, with cornering-aware throttle."""

from racing import RobotCommand, RobotSensors

__author__: str = "730986400"

RACING_NAME: str = "Level 3"
RACING_COLOR: str = "#FEDD00"


def control(sensors: RobotSensors) -> RobotCommand:
    """Steer toward the nearest lookahead point and throttle down for sharp turns."""
    heading_error_degrees: float = sensors.camera.heading_error_degrees
    lookahead_offset_m: float = sensors.camera.lookahead_offsets_m[0]

    steer: float = max(-1.0, min(1.0, (heading_error_degrees / 45.0) + (lookahead_offset_m / 8.0)))

    turn_sharpness: float = abs(heading_error_degrees) / 90.0
    max_speed_mps: float = 18.0 - (6.0 * turn_sharpness)
    throttle: float = max(-1.0, min(1.0, (max_speed_mps - sensors.odometry.speed_mps) / max_speed_mps))

    return RobotCommand(throttle=throttle, steer=steer)
