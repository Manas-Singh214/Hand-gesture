import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import cv2
import numpy as np
from typing import Optional, Tuple, Callable, Any
from config import UI_COLORS

class VideoFeedWidget(tk.Label):
    def __init__(self, parent, width: int = 640, height: int = 480, **kwargs):
        """
        A widget that displays a video feed from a camera with modern styling.
        
        Args:
            parent: Parent widget
            width: Width of the video feed
            height: Height of the video feed
            **kwargs: Additional arguments to pass to the Label constructor
        """
        # Set default background and border
        kwargs.setdefault('bg', UI_COLORS['canvas_bg'])
        kwargs.setdefault('bd', 2)
        kwargs.setdefault('relief', 'ridge')
        
        super().__init__(parent, **kwargs)
        self.width = width
        self.height = height
        self._on_click_callback = None
        
        # Configure the label to maintain aspect ratio
        self.configure(
            width=width,
            height=height,
            compound='center',
            font=('Segoe UI', 10),
            fg=UI_COLORS['text'],
            bg=UI_COLORS['canvas_bg']
        )
        
        # Bind click event
        self.bind("<Button-1>", self._on_click)
        
        # Placeholder for the current photo image
        self.photo = None
        
        # Show placeholder initially
        self.show_placeholder("No camera feed")
        
        # Add hover effect
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Store the original background color for hover effect
        self.original_bg = self['bg']
        
    def _on_enter(self, event):
        self.config(bg=UI_COLORS['header_bg'])
        
    def _on_leave(self, event):
        self.config(bg=self.original_bg)
        
    def show_placeholder(self, text: str):
        """Show a placeholder message when there's no video feed."""
        # Create a blank image with the widget's background color
        img = Image.new('RGB', (self.width, self.height), color=self['bg'])
        draw = ImageDraw.Draw(img)
        
        # Add text in the center
        try:
            font = ImageFont.truetype("segoeui.ttf", 14)
        except:
            font = ImageFont.load_default()
            
        # Calculate text size and position
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (self.width - text_width) // 2
        y = (self.height - text_height) // 2
        
        # Draw the text
        draw.text((x, y), text, fill=UI_COLORS['text'], font=font)
        
        # Convert to PhotoImage and update the label
        self.photo = ImageTk.PhotoImage(image=img)
        self.config(image=self.photo)
    
    def update_frame(self, frame) -> None:
        """
        Update the video feed with a new frame.
        
        Args:
            frame: The frame to display (numpy array in BGR format)
        """
        if frame is None:
            self.show_placeholder("No frame received")
            return
            
        try:
            # Convert the frame to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Calculate aspect ratio
            h, w = frame_rgb.shape[:2]
            aspect_ratio = w / h
            
            # Calculate new dimensions while maintaining aspect ratio
            new_w = self.width
            new_h = int(new_w / aspect_ratio)
            
            # If the calculated height is greater than available height, adjust width
            if new_h > self.height:
                new_h = self.height
                new_w = int(new_h * aspect_ratio)
            
            # Resize the frame
            frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
            
            # Create a blank canvas with the widget's background color
            canvas = np.full((self.height, self.width, 3), 
                           [x * 255 for x in self._hex_to_rgb(UI_COLORS['canvas_bg'])], 
                           dtype=np.uint8)
            
            # Calculate position to center the frame
            x_offset = (self.width - new_w) // 2
            y_offset = (self.height - new_h) // 2
            
            # Place the frame on the canvas
            canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame_resized
            
            # Add a subtle border
            border_color = [x * 255 for x in self._hex_to_rgb(UI_COLORS['primary'])]
            border_size = 2
            cv2.rectangle(canvas, 
                         (0, 0), 
                         (self.width-1, self.height-1), 
                         border_color, 
                         border_size)
            
            # Convert to PhotoImage
            image = Image.fromarray(canvas)
            self.photo = ImageTk.PhotoImage(image=image)
            
            # Update the label
            self.config(image=self.photo)
            self.image = self.photo  # Keep a reference
            
        except Exception as e:
            print(f"Error updating video frame: {e}")
            self.show_placeholder("Error displaying frame")
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB values between 0 and 1."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    def set_click_callback(self, callback: Callable[[int, int], Any]) -> None:
        """
        Set a callback function to be called when the widget is clicked.
        The callback will receive the x and y coordinates of the click.
        """
        self._on_click_callback = callback
    
    def _on_click(self, event) -> None:
        """Handle click events on the video feed."""
        if self._on_click_callback:
            self._on_click_callback(event.x, event.y)
    
    def get_size(self) -> Tuple[int, int]:
        """Get the size of the video feed."""
        return (self.width, self.height)
