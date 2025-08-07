import tkinter as tk

class KeybindsInfoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keybinds Info")
        self.root.overrideredirect(True)

        transparent_color = "black"
        self.root.config(bg=transparent_color)
        self.root.wm_attributes('-transparentcolor', transparent_color)
        self.root.wm_attributes("-topmost", True)

        # Text with all keybinds & combos info from your code
        self.keybinds_text = (
            "Keybinds and Combinations:\n"
            "\n"
            "1 : Decrease main stamina by 0.5\n"
            "Double-tap 1 : Toggle auto decrease main stamina\n"
            "\n"
            "2 : Increase main stamina by 0.5\n"
            "3 : Reset main stamina\n"
            "\n"
            "q : Increase extra stamina by 5\n"
            "e : Decrease extra stamina by 0.5\n"
            "Double-tap e : Toggle auto decrease extra stamina\n"
            "r : Reset extra stamina to max (100)\n"
            "\n"
            "w : Toggle main stamina regeneration\n"
            "o : Open effect adjuster window\n"
            "\n"
            "4,5,6,7,8,9,0,minus : Adjust respective effects\n"
            "   (Weight, Hunger, Damage, Poison, Cold, Heat, Drowsy, Curse)\n"
            "Backtick + effect key : Reset that effect\n"
            "Single click effect key : Stop continuous decrease\n"
            "Double click effect key : Decrease effect by 0.5\n"
            "Triple click effect key : Toggle continuous decrease for effect\n"
            "\n"
            "= (equal) : Toggle hunger auto increase pause/resume\n"
            "Right bracket ] : Reset hunger timer\n"
            "\n"
            "` (backtick) : Holding + effect key resets that effect\n"
            "\n"
            "Mouse Drag : Move the window\n"
        )

        # Frame with gray background to hold the text and buttons
        self.bg_frame = tk.Frame(root, bg="gray")
        self.bg_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.label = tk.Label(self.bg_frame, text=self.keybinds_text, fg='white', bg="gray",
                              font=('Helvetica', 14), justify='left')
        self.label.pack(padx=20, pady=(20, 10))

        btn_frame = tk.Frame(self.bg_frame, bg="gray")
        btn_frame.pack(pady=(0, 20))

        self.close_button = tk.Button(btn_frame, text="Close", command=self.root.destroy)
        self.close_button.pack(side="left", padx=10)

        self.increase_button = tk.Button(btn_frame, text="Bigger", command=self.increase_size)
        self.increase_button.pack(side="left", padx=10)

        self.decrease_button = tk.Button(btn_frame, text="Smaller", command=self.decrease_size)
        self.decrease_button.pack(side="left", padx=10)

        # Enable dragging the window by the label area as well
        self._drag_data = {"x": 0, "y": 0}
        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        # Default font size
        self.font_size = 14

    def increase_size(self):
        if self.font_size < 30:
            self.font_size += 2
            self.label.config(font=('Helvetica', self.font_size))

    def decrease_size(self):
        if self.font_size > 8:
            self.font_size -= 2
            self.label.config(font=('Helvetica', self.font_size))

    def start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KeybindsInfoApp(root)
    root.mainloop()
