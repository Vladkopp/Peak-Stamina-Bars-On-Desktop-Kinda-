import tkinter as tk
import time

class StaminaBarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PEAK Stamina Bar")

        # Remove window decorations for clean look
        self.root.overrideredirect(True)

        # Transparent background setup
        transparent_color = "black"
        self.root.config(bg=transparent_color)
        self.root.wm_attributes('-transparentcolor', transparent_color)

        # Make window always stay on top
        self.root.wm_attributes("-topmost", True)

        # Base stamina and current stamina
        self.base_max_stamina = 100.0
        self.current_stamina = 100.0

        # Effects data: color, value, continuous decrease toggle, poison timers
        self.effects = {
            "4": {"name": "Weight", "color": "brown", "value": 0.0, "continuous_decrease": False},
            "5": {"name": "Hunger", "color": "yellow", "value": 0.0, "continuous_decrease": False},
            "6": {"name": "Damage", "color": "red", "value": 0.0, "continuous_decrease": False},
            "7": {"name": "Poison", "color": "purple", "value": 0.0, "continuous_decrease": False,
                  "poison_timer": 30.0, "poison_active": False, "poison_decrement_interval": 10.0, "last_poison_tick": 0.0},
            "8": {"name": "Cold", "color": "cyan", "value": 0.0, "continuous_decrease": False},
            "9": {"name": "Heat", "color": "dark red", "value": 0.0, "continuous_decrease": False},
            "0": {"name": "Drowsy", "color": "pink", "value": 0.0, "continuous_decrease": False},
            "minus": {"name": "Curse", "color": "purple", "value": 0.0, "continuous_decrease": False}  # bound to "-" key
        }

        # Include 'minus' key in effect keys list
        self.effect_keys = ['4','5','6','7','8','9','0','minus']

        # Canvas and bar size
        self.canvas_width = 480
        self.canvas_height = 120
        self.bar_x_start = 15
        self.bar_x_end = 465
        self.bar_y_start = 60
        self.bar_y_end = 90
        self.bar_length = self.bar_x_end - self.bar_x_start
        self.bar_height = self.bar_y_end - self.bar_y_start

        # Create canvas with transparent bg
        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height,
                                bg=transparent_color, highlightthickness=0)
        self.canvas.pack()

        # Background stamina bar (grey)
        self.stamina_bar_back = self.canvas.create_rectangle(
            self.bar_x_start, self.bar_y_start,
            self.bar_x_end, self.bar_y_end,
            fill='grey', outline='white')

        # Foreground stamina bar (green)
        self.stamina_bar_front = self.canvas.create_rectangle(
            self.bar_x_start, self.bar_y_start,
            self.bar_x_end, self.bar_y_end,
            fill='green', outline='')

        # Create effect bars stacked vertically inside stamina bar height
        self.effect_bars = {}
        self.effect_texts = {}
        effect_bar_height = self.bar_height / len(self.effect_keys)
        for i, key in enumerate(self.effect_keys):
            y1 = self.bar_y_start + i * effect_bar_height
            y2 = y1 + effect_bar_height
            rect_id = self.canvas.create_rectangle(
                self.bar_x_start, y1, self.bar_x_start, y2,
                fill=self.effects[key]['color'], outline='')
            self.effect_bars[key] = rect_id
            # Create effect text with smaller font size for fit, showing values only
            txt_id = self.canvas.create_text(
                self.bar_x_start + 5,  # left padding inside bar
                (y1 + y2) / 2,
                text="",
                anchor='w',
                fill='white',
                font=('Helvetica', 7, 'bold')  # smaller font to fit in thin bar
            )
            self.effect_texts[key] = txt_id

        # Stamina text centered inside stamina bar (higher layer)
        self.text = self.canvas.create_text(
            (self.bar_x_start + self.bar_x_end)//2,
            self.bar_y_start + self.bar_height / 2,
            fill='white', font=('Helvetica', 24, 'bold'),
            text=self._stamina_text())
        self.canvas.tag_raise(self.text)

        # Status label below canvas
        self.status_label = tk.Label(root, text="", fg='white', bg=transparent_color, font=('Helvetica', 16))
        self.status_label.pack(pady=5)

        # Bind stamina keys 1, 2, 3
        self.root.bind('1', self.decrease_stamina)
        self.root.bind('2', self.increase_stamina)
        self.root.bind('3', self.reset_stamina)

        # Bind effect keys press/release
        for key in self.effect_keys:
            self.root.bind(f'<KeyPress-{key}>', self.effect_key_press)
            self.root.bind(f'<KeyRelease-{key}>', self.effect_key_release)

        # Backtick key for reset (alone or combined)
        self.backtick_held = False
        self.root.bind('<KeyPress-`>', self.backtick_press)
        self.root.bind('<KeyRelease-`>', self.backtick_release)

        # Dragging variables
        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        # Held keys and continuous decrease states
        self.held_keys = set()
        self.effects_continuous_decrease = {k: False for k in self.effect_keys}

        # Click times for multi-click detection
        self.click_times = {k: [] for k in self.effect_keys}

        self.update_loop_interval = 50  # ms
        self.update_loop()

    def _stamina_text(self):
        return f"Stamina: {self.current_stamina:.1f} / {self.effective_max_stamina():.1f}"

    def effective_max_stamina(self):
        total = self.base_max_stamina
        for k, eff in self.effects.items():
            if k == '7':  # poison does not reduce max stamina directly
                continue
            total -= eff['value']
        return max(total, 0.0)

    def update_stamina_bar(self):
        max_stam = self.effective_max_stamina()
        if self.current_stamina > max_stam:
            self.current_stamina = max_stam

        bar_width = 0
        if max_stam > 0:
            bar_width = (self.current_stamina / max_stam) * self.bar_length

        # Update green stamina bar width and color
        self.canvas.coords(self.stamina_bar_front,
                           self.bar_x_start, self.bar_y_start,
                           self.bar_x_start + bar_width, self.bar_y_end)

        pct = (self.current_stamina / max_stam) if max_stam > 0 else 0
        if pct > 0.6:
            color = "green"
        elif pct > 0.3:
            color = "yellow"
        else:
            color = "red"
        self.canvas.itemconfig(self.stamina_bar_front, fill=color)

        effect_bar_height = self.bar_height / len(self.effect_keys)

        for i, key in enumerate(self.effect_keys):
            val = self.effects[key]['value']
            length_ratio = max(0.0, min(val / self.base_max_stamina, 1.0))

            y1 = self.bar_y_start + i * effect_bar_height
            y2 = y1 + effect_bar_height

            if self.current_stamina > 0:
                # Effects overlay inside green bar width
                effect_width = bar_width * length_ratio
                x1 = self.bar_x_start
                x2 = x1 + effect_width
            else:
                # Stamina zero, effects extend beyond right edge
                x1 = self.bar_x_end
                effect_width = self.bar_length * length_ratio
                x2 = x1 + effect_width

            self.canvas.coords(self.effect_bars[key], x1, y1, x2, y2)

            # Effect text update: only show numeric value
            text = f"{val:.1f}"

            text_x = x1 + 5  # left padding
            max_text_x = x2 - 2
            if text_x > max_text_x:
                text_x = max_text_x
            text_y = (y1 + y2) / 2

            self.canvas.coords(self.effect_texts[key], text_x, text_y)
            self.canvas.itemconfig(self.effect_texts[key], text=text)

        # Bring stamina text on top
        self.canvas.tag_raise(self.text)
        self.canvas.itemconfig(self.text, text=self._stamina_text())

    def decrease_stamina(self, event=None):
        dec_amount = 0.5
        new_val = self.current_stamina - dec_amount
        if new_val < 0:
            new_val = 0.0
        self.current_stamina = new_val
        self.update_stamina_bar()

    def increase_stamina(self, event=None):
        inc_amount = 0.5
        max_stam = self.effective_max_stamina()
        new_val = self.current_stamina + inc_amount
        if new_val > max_stam:
            new_val = max_stam
        self.current_stamina = new_val
        self.update_stamina_bar()

    def reset_stamina(self, event=None):
        self.current_stamina = self.effective_max_stamina()
        self.update_stamina_bar()

    # Backtick press/release for combined reset key behavior
    def backtick_press(self, event):
        self.backtick_held = True

    def backtick_release(self, event):
        if not self.held_keys:
            self.reset_last_effect()
        self.backtick_held = False

    # Effect keypress handler (hold, clicks, combined backtick reset)
    def effect_key_press(self, event):
        key = event.keysym
        if key not in self.effect_keys:
            return

        if self.backtick_held:
            if self.effects[key]['value'] > 0:
                self.effects[key]['value'] = 0.0
                if key == '7':  # Reset poison timers
                    self.effects[key]['poison_timer'] = 30.0
                    self.effects[key]['poison_active'] = False
                    self.effects[key]['last_poison_tick'] = 0.0
                self.effects_continuous_decrease[key] = False
                self.show_effect_status(key, f"Reset effect '{self.effects[key]['name']}' (with backtick)")
                max_stam = self.effective_max_stamina()
                if self.current_stamina > max_stam:
                    self.current_stamina = max_stam
                self.update_stamina_bar()
            return

        if key not in self.held_keys:
            self.held_keys.add(key)

        now = time.time()
        times = self.click_times[key]
        times.append(now)
        if len(times) > 3:
            times.pop(0)

        click_type = self.detect_click_type(times)
        if click_type == 1:
            if self.effects_continuous_decrease[key]:
                self.effects_continuous_decrease[key] = False
                self.show_effect_status(key, f"Stopped continuous decrease for {self.effects[key]['name']}")
        elif click_type == 2:
            self.change_effect_value(key, -0.5)
            self.show_effect_status(key, f"Decreased {self.effects[key]['name']} by 0.5 (double click)")
        elif click_type >= 3:
            current_state = self.effects_continuous_decrease[key]
            self.effects_continuous_decrease[key] = not current_state
            action = "Started" if not current_state else "Stopped"
            self.show_effect_status(key, f"{action} continuous decrease for {self.effects[key]['name']} (triple click)")

        self.update_stamina_bar()

    def effect_key_release(self, event):
        key = event.keysym
        if key in self.held_keys:
            self.held_keys.remove(key)

    # Multi-click detection helper
    def detect_click_type(self, timestamps):
        threshold = 0.4
        if len(timestamps) == 1:
            return 1
        elif len(timestamps) == 2:
            return 2 if timestamps[-1] - timestamps[-2] <= threshold else 1
        elif len(timestamps) == 3:
            t1, t2, t3 = timestamps[-3], timestamps[-2], timestamps[-1]
            if t3 - t1 <= threshold*2:
                return 3
            elif t3 - t2 <= threshold:
                return 2
            else:
                return 1
        return 1

    # Change effect's value clamped [0, base_max_stamina]
    def change_effect_value(self, key, delta):
        old_val = self.effects[key]['value']
        new_val = min(max(old_val + delta, 0.0), self.base_max_stamina)
        self.effects[key]['value'] = new_val

        max_stam = self.effective_max_stamina()
        if self.current_stamina > max_stam:
            self.current_stamina = max_stam

    # Show temporary status message
    def show_effect_status(self, key, msg):
        self.status_label.config(text=msg)
        self.root.after(3000, self.clear_status)

    def clear_status(self):
        self.status_label.config(text="")

    # Reset last active effect in reverse key order
    def reset_last_effect(self, event=None):
        for key in reversed(self.effect_keys):
            if self.effects[key]['value'] > 0:
                self.effects[key]['value'] = 0.0
                if key == '7':
                    self.effects[key]['poison_timer'] = 30.0
                    self.effects[key]['poison_active'] = False
                    self.effects[key]['last_poison_tick'] = 0.0
                self.effects_continuous_decrease[key] = False
                self.show_effect_status(key, f"Reset effect '{self.effects[key]['name']}'")
                max_stam = self.effective_max_stamina()
                if self.current_stamina > max_stam:
                    self.current_stamina = max_stam
                self.update_stamina_bar()
                return
        self.show_effect_status('', "No active effects to reset")

    # Main update loop called every ~50ms
    def update_loop(self):
        now = time.time()

        # Increase held effect values (~10 increments per second)
        inc_rate = 0.5 * (self.update_loop_interval / 1000) * 10
        for key in list(self.held_keys):
            self.change_effect_value(key, inc_rate)

        # Continuous decrease effects (~5 decrements per second)
        dec_rate = 0.5 * (self.update_loop_interval / 1000) * 5
        for key, continuous in self.effects_continuous_decrease.items():
            if continuous:
                self.change_effect_value(key, -dec_rate)

        # Poison effect special behavior: after 30s countdown starts draining its own value by 3.5 every 10s
        poison = self.effects['7']
        if poison['value'] > 0:
            if not poison.get('poison_active', False):
                poison['poison_timer'] -= self.update_loop_interval / 1000
                if poison['poison_timer'] <= 0:
                    poison['poison_active'] = True
                    poison['last_poison_tick'] = now
            else:
                if now - poison['last_poison_tick'] >= poison['poison_decrement_interval']:
                    new_val = poison['value'] - 3.5
                    if new_val < 0:
                        new_val = 0.0
                        poison['poison_timer'] = 30.0
                        poison['poison_active'] = False
                    poison['value'] = new_val
                    poison['last_poison_tick'] = now

        self.update_stamina_bar()
        self.root.after(self.update_loop_interval, self.update_loop)

    # Drag handlers
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
    app = StaminaBarApp(root)
    root.mainloop()
