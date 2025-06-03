# animation.py
import pygame

class Animation:
    def __init__(self, spritesheet, frame_width, frame_height, frame_count, frame_duration):
        self.frames = []
        self.frame_duration = frame_duration
        self.elapsed_time = 0
        self.current_frame = 0
        
        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        
        max_frames = min(frame_count, sheet_width // frame_width)
        
        if max_frames == 0:
            print(f"Warning: Frame width {frame_width} exceeds sheet width {sheet_width}")
            # Create a dummy frame to avoid crashes
            self.frames.append(pygame.Surface((frame_width, frame_height), pygame.SRCALPHA))
        else:
            for i in range(max_frames):
                # Ensure we don't exceed sheet boundaries
                if (i * frame_width) + frame_width <= sheet_width:
                    frame = spritesheet.subsurface((i * frame_width, 0, frame_width, frame_height))
                    self.frames.append(frame)
                else:
                    print(f"Warning: Frame {i} exceeds sheet boundaries")
        
        if not self.frames:
            self.frames.append(pygame.Surface((frame_width, frame_height), pygame.SRCALPHA))

    def update(self, dt):
        self.elapsed_time += dt
        if self.elapsed_time >= self.frame_duration:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.elapsed_time = 0

    def get_frame(self):
        return self.frames[self.current_frame]