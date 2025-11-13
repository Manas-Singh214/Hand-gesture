import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from typing import Callable, Optional, Dict, Any
from config import UI_COLORS
from .video_feed_widget import VideoFeedWidget
from PIL import Image, ImageTk
import os

# Custom style for ttk widgets
def configure_styles():
    style = ttk.Style()
    
    # Configure the main window style
    style.configure('.', background=UI_COLORS['background'])
    
    # Configure button styles
    style.configure('TButton',
                   padding=6,
                   relief='flat',
                   background=UI_COLORS['button_bg'],
                   foreground=UI_COLORS['button_fg'],
                   font=('Segoe UI', 10, 'bold'))
    
    style.map('TButton',
             background=[('active', UI_COLORS['button_active']),
                       ('pressed', UI_COLORS['accent'])],
             foreground=[('active', 'white')])
    
    # Configure label frames
    style.configure('TLabelframe',
                   background=UI_COLORS['background'],
                   foreground=UI_COLORS['text'],
                   borderwidth=2,
                   relief='groove')
    
    style.configure('TLabelframe.Label',
                   background=UI_COLORS['header_bg'],
                   foreground=UI_COLORS['text'],
                   font=('Segoe UI', 10, 'bold'))
    
    # Configure labels
    style.configure('TLabel',
                   background=UI_COLORS['background'],
                   foreground=UI_COLORS['text'],
                   font=('Segoe UI', 10))
    
    # Configure paned window
    style.configure('TPanedwindow',
                   background=UI_COLORS['background'])
    
    # Configure scrollbar
    style.configure('Vertical.TScrollbar',
                   background=UI_COLORS['secondary'],
                   troughcolor=UI_COLORS['background'],
                   arrowcolor=UI_COLORS['text'],
                   bordercolor=UI_COLORS['background'])
    
    # Configure entry
    style.configure('TEntry',
                  fieldbackground=UI_COLORS['canvas_bg'],
                  foreground=UI_COLORS['text'],
                  insertcolor=UI_COLORS['text'])
    
    # Configure combobox
    style.map('TCombobox',
             fieldbackground=[('readonly', UI_COLORS['canvas_bg'])],
             selectbackground=[('readonly', UI_COLORS['primary'])],
             selectforeground=[('readonly', 'white')])

class MainWindow:
    def __init__(self, root, title: str = "Sign-to-Speech Translator"):
        """
        Initialize the main application window.
        
        Args:
            root: The root Tkinter window
            title: Window title
        """
        self.root = root
        self.root.title(title)
        self.root.geometry("1200x800")
        
        # Set window icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load window icon: {e}")
        
        # Configure the root window style
        self.root.configure(bg=UI_COLORS['background'])
        self.root.option_add('*TCombobox*Listbox.background', UI_COLORS['canvas_bg'])
        self.root.option_add('*TCombobox*Listbox.foreground', UI_COLORS['text'])
        self.root.option_add('*TCombobox*Listbox.selectBackground', UI_COLORS['primary'])
        self.root.option_add('*TCombobox*Listbox.selectForeground', 'white')
        
        # Configure ttk styles
        configure_styles()
        
        # Set window minimum size
        self.root.minsize(1000, 700)
        
        # Status variables
        self.status_text = tk.StringVar()
        self.recognized_text = tk.StringVar()
        
        # Create UI components
        self._create_widgets()
        
        # Initialize callbacks
        self.on_add_gesture_cb = None
        self.on_edit_gesture_cb = None
        self.on_delete_gesture_cb = None
        self.on_open_camera_cb = None
    
    def _create_widgets(self) -> None:
        # Create main container with a paned window for resizable panels
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL, style='TPanedwindow')
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for video feed and controls
        left_panel = ttk.Frame(self.main_paned, style='TFrame')
        
        # Create video feed frame with a border
        video_container = ttk.LabelFrame(left_panel, text="Camera Feed", padding=5, style='TLabelframe')
        video_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.video_feed = VideoFeedWidget(video_container, width=800, height=600, bg=UI_COLORS['canvas_bg'])
        self.video_feed.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        # Create control panel with a modern look
        control_frame = ttk.Frame(left_panel, style='TFrame')
        control_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Add control buttons with icons and better spacing
        ttk.Style().configure('BlackText.TButton', foreground='black')
        
        ttk.Button(
            control_frame, 
            text="📷 Open Camera", 
            command=self._on_open_camera,
            width=15,
            padding=8,
            style='BlackText.TButton'
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(
            control_frame, 
            text="➕ Add Gesture", 
            command=self._on_add_gesture,
            width=15,
            padding=8,
            style='BlackText.TButton'
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Add left panel to main paned window
        self.main_paned.add(left_panel, weight=3)  # Give more space to video feed
        
        # Right panel for gesture list and recognized text
        right_panel = ttk.Frame(self.main_paned, style='TFrame')
        
        # Gesture list frame with modern styling
        gesture_list_frame = ttk.LabelFrame(
            right_panel, 
            text="✨ Available Gestures", 
            padding=10,
            style='TLabelframe'
        )
        gesture_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a canvas with scrollbar for the gesture list
        canvas = tk.Canvas(
            gesture_list_frame, 
            height=300,
            bg=UI_COLORS['canvas_bg'],
            highlightthickness=0
        )
        
        # Custom scrollbar with modern look
        style = ttk.Style()
        style.configure('Custom.Vertical.TScrollbar', 
                       arrowcolor=UI_COLORS['text'],
                       background=UI_COLORS['secondary'])
        
        scrollbar = ttk.Scrollbar(
            gesture_list_frame, 
            orient="vertical", 
            command=canvas.yview,
            style='Custom.Vertical.TScrollbar'
        )
        
        self.gesture_list_frame = ttk.Frame(canvas, style='TFrame')
        self.gesture_list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.gesture_list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=2)
        
        # Recognized text display with modern styling
        recognized_frame = ttk.LabelFrame(
            right_panel, 
            text="🔊 Recognized Text", 
            padding=10,
            style='TLabelframe'
        )
        recognized_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Styled label for recognized text
        self.recognized_label = ttk.Label(
            recognized_frame, 
            textvariable=self.recognized_text, 
            wraplength=250,
            justify=tk.CENTER,
            font=('Segoe UI', 10, 'bold'),
            foreground=UI_COLORS['highlight'],
            background=UI_COLORS['canvas_bg'],
            padding=10,
            relief='groove',
            borderwidth=1
        )
        self.recognized_label.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add right panel to main paned window
        self.main_paned.add(right_panel, weight=1)
        
        # Add status bar at the bottom with modern styling
        status_bar = ttk.Frame(self.root, style='TFrame')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        
        # Status label with subtle gradient background
        self.status_var = tk.StringVar()
        status_label = ttk.Label(
            status_bar, 
            textvariable=self.status_var,
            anchor=tk.W,
            font=('Segoe UI', 9),
            background=UI_COLORS['header_bg'],
            foreground=UI_COLORS['text'],
            padding=(10, 5, 10, 5),
            relief='flat'
        )
        status_label.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        # Add version info
        version_label = ttk.Label(
            status_bar,
            text="Sign-to-Speech v1.0",
            anchor=tk.E,
            font=('Segoe UI', 8),
            foreground='#95a5a6',
            padding=(0, 5, 10, 5)
        )
        version_label.pack(side=tk.RIGHT)
        
        # Set initial status
        self.status_var.set("✅ Ready")
        
        # Store the gesture labels for updating later
        self.gesture_labels = []
        
        # Initialize with empty gestures
        self.update_gesture_list({})
    
    def update_gesture_list(self, gestures: Dict[str, Dict[str, Any]]) -> None:
        """
        Update the gesture list in the UI.
        
        Args:
            gestures: Dictionary of gestures with their details
        """
        # Clear existing gesture labels
        for widget in self.gesture_list_frame.winfo_children():
            widget.destroy()
        
        if not gestures:
            ttk.Label(
                self.gesture_list_frame,
                text="No gestures found. Add some gestures to get started!",
                wraplength=250,
                justify=tk.CENTER,
                foreground="gray"
            ).pack(padx=10, pady=10, fill=tk.X)
            return
        
        # Add each gesture to the list
        for gesture_id, gesture in gestures.items():
            frame = ttk.Frame(self.gesture_list_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # Gesture name and details
            details = f"{gesture.get('name', 'Unnamed Gesture')}"
            if 'message' in gesture and gesture['message']:
                details += f"\n💬 {gesture['message']}"
            
            label = ttk.Label(
                frame,
                text=details,
                anchor=tk.W,
                justify=tk.LEFT,
                padding=(10, 5, 10, 5),
                relief=tk.GROOVE,
                borderwidth=1
            )
            label.pack(fill=tk.X, expand=True)
            
            # Store the gesture ID with the label
            label.gesture_id = gesture_id
            self.gesture_labels.append(label)
    
    # Callback setters
    def set_add_gesture_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for the 'Add Gesture' button."""
        self.on_add_gesture_cb = callback
    
    def set_edit_gesture_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for the 'Edit Gesture' button."""
        self.on_edit_gesture_cb = callback
    
    def set_delete_gesture_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for the 'Delete Gesture' button."""
        self.on_delete_gesture_cb = callback
    
    def set_open_camera_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for the 'Open Camera' button."""
        self.on_open_camera_cb = callback
    
    # Button handlers
    def _on_open_camera(self):
        """Handle 'Open Camera' button click."""
        if self.on_open_camera_cb:
            self.on_open_camera_cb()
            
    def _on_add_gesture(self):
        """Handle 'Add Gesture' button click."""
        if self.on_add_gesture_cb:
            self.on_add_gesture_cb()
    
    def _on_edit_gesture(self) -> None:
        """Handle 'Edit Gesture' button click."""
        selected = self.gesture_tree.selection()
        if not selected:
            self.show_error("No Selection", "Please select a gesture to edit")
            return
        
        if self.on_edit_gesture_cb:
            self.on_edit_gesture_cb(selected[0])
    
    def _on_delete_gesture(self) -> None:
        """Handle 'Delete Gesture' button click."""
        selected = self.gesture_tree.selection()
        if not selected:
            self.show_error("No Selection", "Please select a gesture to delete")
            return
        
        gesture_id = selected[0]
        gesture_name = self.gesture_tree.item(gesture_id, "values")[0]
        
        if self.show_confirm(
            "Confirm Delete",
            f"Are you sure you want to delete the gesture: {gesture_name}?"
        ):
            if self.on_delete_gesture_cb:
                self.on_delete_gesture_cb(gesture_id)
    
        self.gesture_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add gestures to the treeview
        for gesture_id, gesture in gestures.items():
            self.gesture_tree.insert(
                "",
                "end",
                iid=gesture_id,
                values=(
                    gesture.get("name", "Unnamed"),
                    gesture.get("message", "")
                )
            )
        
        # Add context menu for right-click actions
        self.setup_gesture_context_menu()
        
        # Bind double-click to edit
        self.gesture_tree.bind("<Double-1>", self.on_gesture_double_click)
        
        # Update the canvas scroll region
        self.gesture_list_frame.update_idletasks()
    
    def setup_gesture_context_menu(self) -> None:
        """Set up the right-click context menu for gestures."""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Edit", command=self._on_edit_gesture)
        self.context_menu.add_command(label="Delete", command=self._on_delete_gesture)
        
        # Bind right-click event
        self.gesture_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event) -> None:
        """Show the context menu on right-click."""
        item = self.gesture_tree.identify_row(event.y)
        if item:
            self.gesture_tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()
    
    def on_gesture_double_click(self, event) -> None:
        """Handle double-click on a gesture to edit it."""
        item = self.gesture_tree.identify_row(event.y)
        if item:
            self._on_edit_gesture()
    
    def update_video_frame(self, frame) -> None:
        """Update the video feed with a new frame."""
        self.video_feed.update_frame(frame)
    
    def set_status(self, message: str) -> None:
        """Update the status message."""
        self.status_var.set(message)
    
    def set_recognized_text(self, text: str) -> None:
        """Update the recognized text display."""
        self.recognized_text.set(text)
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        tooltip = ttk.Label(
            widget, 
            text=text, 
            background='#ffffe0',
            relief='solid',
            borderwidth=1,
            padding=5,
            wraplength=200
        )
        tooltip.place(relx=1.0, rely=1.0, anchor='ne')
        tooltip.place_forget()
        
        def show_tooltip(event):
            tooltip.place(relx=1.0, rely=1.0, anchor='ne')
        
        def hide_tooltip(event):
            tooltip.place_forget()
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
        return tooltip
    
    def show_error(self, title: str, message: str) -> None:
        """Show an error message dialog."""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str) -> None:
        """Show an information message dialog."""
        messagebox.showinfo(title, message)
    
    def show_confirm(self, title: str, message: str) -> bool:
        """Show a confirmation dialog."""
        return messagebox.askyesno(title, message)
    
    def get_text_input(self, title: str, prompt: str, default: str = "") -> Optional[str]:
        """Show a dialog to get text input from the user."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        
        ttk.Label(dialog, text=prompt).pack(padx=10, pady=5)
        
        entry_var = tk.StringVar(value=default)
        entry = ttk.Entry(dialog, textvariable=entry_var, width=40)
        entry.pack(padx=10, pady=5)
        entry.focus()
        
        result = None
        
        def on_ok():
            nonlocal result
            result = entry_var.get()
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Make the dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return result
        
    def get_choice(self, title: str, prompt: str, options: list) -> Optional[str]:
        """Show a dialog to select one option from a list."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        
        ttk.Label(dialog, text=prompt).pack(padx=10, pady=5)
        
        selected = tk.StringVar(value="")
        
        # Create radio buttons for each option
        for option in options:
            rb = ttk.Radiobutton(
                dialog, 
                text=option,
                variable=selected,
                value=option
            )
            rb.pack(anchor=tk.W, padx=20, pady=2)
        
        result = None
        
        def on_ok():
            nonlocal result
            result = selected.get()
            dialog.destroy()
        
        def on_cancel():
            nonlocal result
            result = None
            dialog.destroy()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Make the dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
        
        return result
