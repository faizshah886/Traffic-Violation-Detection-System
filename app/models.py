"""
Data models for Traffic Violation System
"""

# Fine structure for different violations
FINE_STRUCTURE = {
    "helmet_violation": 1000,
    "triple_riding": 1500,
    "red_light_crossing": 2000
}

class ViolationType:
    HELMET = "helmet_violation"
    TRIPLE_RIDING = "triple_riding"
    RED_LIGHT = "red_light_crossing"
