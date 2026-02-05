"""
Traffic Light Simulator
Simulates red/green light cycles for testing violation detection
"""
import time
from datetime import datetime

class TrafficLightSimulator:
    def __init__(self, red_duration=10, green_duration=15, video_fps=30):
        """
        Initialize traffic light simulator
        Args:
            red_duration: Seconds for red light (default 10)
            green_duration: Seconds for green light (default 15)
            video_fps: Frames per second of the video (for frame-based timing)
        """
        self.red_duration = red_duration
        self.green_duration = green_duration
        self.cycle_duration = red_duration + green_duration
        self.video_fps = video_fps
        self.current_frame = 0
        self.current_state = 'RED'  # Start with red
        
    def update_frame(self, frame_number):
        """Update the current frame number"""
        self.current_frame = frame_number
        
    def get_current_state(self):
        """
        Get current traffic light state based on video time
        Returns: 'RED' or 'GREEN'
        """
        # Calculate video time in seconds
        video_time = self.current_frame / self.video_fps
        position_in_cycle = video_time % self.cycle_duration
        
        if position_in_cycle < self.red_duration:
            self.current_state = 'RED'
        else:
            self.current_state = 'GREEN'
            
        return self.current_state
    
    def is_red(self):
        """Check if light is currently red"""
        return self.get_current_state() == 'RED'
    
    def is_green(self):
        """Check if light is currently green"""
        return self.get_current_state() == 'GREEN'
    
    def get_time_remaining(self):
        """Get seconds remaining in current state"""
        video_time = self.current_frame / self.video_fps
        position_in_cycle = video_time % self.cycle_duration
        
        if self.current_state == 'RED':
            return self.red_duration - position_in_cycle
        else:
            return self.cycle_duration - position_in_cycle
    
    def reset(self):
        """Reset the timer"""
        self.current_frame = 0
        
    def set_durations(self, red_duration, green_duration):
        """Update light durations"""
        self.red_duration = red_duration
        self.green_duration = green_duration
        self.cycle_duration = red_duration + green_duration
