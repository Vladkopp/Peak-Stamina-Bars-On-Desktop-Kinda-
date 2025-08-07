import tkinter as tk
from tkinter import messagebox
import time

class StaminaBarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PEAK Stamina Bar")
        self.root.configure(bg="black")

        # Base stamina values
        self.base_max_stamina = 100.0
        self.current_stamina = 100.0

        # Effects dict
        self.effects = {
            "4": {"name": "Weight", "color": "brown", "value": 0.0, "continuous_decrease": False},
            "5": {"name": "Hunger", "color": "yellow", "value": 0.0, "continuous_decrease": False},
            "6": {"name": "Damage", "color": "red", "value": 0.0, "continuous_decrease": False},
            "7": {"name": "Poison", "color": "purple", "value": 0.0, "continuous_decrease": False,
                  "poison_timer": 30.0, "poison_active": False, "poison_decrement_interval": 10.0, "last_poison_tick": 0.0},
            "8": {"name": "Cold", "color": "cyan", "value": 0.0, "continuous_decrease": False},
            "9": {"name": "Heat", "color": "dark red", "value": 0.0, "continuous_decrease": False},
            "0": {"name": "Drowsy", "color": "pink", "value": 0.0, "continuous_decrease": False},
            "c": {"name": "Curse", "color": "purple", "value": 0.0, "continuous_decrease": False}
        }

        self.effect_keys = ['4', '5', '6', '7', '8', '9', '0']

        self.canvas_width = 320
        self.canvas_height = 80
        self.bar_x_start = 10
        self.bar_x_end = 310
        self.bar_y_start = 40
        self.bar_y_end = 60
        self.bar_length = self.bar_x_end - self.bar_x_start

        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height, bg='black', highlightthickness=0)
        self.canvas.pack()

        self.stamina_bar_back = self.canvas.create_rectangle(self.bar_x_start, self.bar_y_start,
                                                            self.bar_x_end, self.bar_y_end,
                                                            fill='grey', outline='white')

        self.stamina_bar_front = self.canvas.create_rectangle(self.bar_x_start, self.bar_y_start,
                                                             self.bar_x_end, self.bar_y_end,
                                                             fill='green', outline='')

        self.effect_bars = {}
        bar_height = 6
        gap = 2
        y_start = self.bar_y_start - bar_height - gap
        for i, key in enumerate(self.effect_keys):
            y1 = y_start - i * (bar_height + gap)
            y2 = y1 + bar_height
            rect_id = self.canvas.create_rectangle(self.bar_x_start, y1, self.bar_x_start, y2,
                                                   fill=self.effects[key]["color"], outline='')
            self.effect_bars[key] = rect_id

        self.text = self.canvas.create_text(self.canvas_width // 2, self.bar_y_end + 15,
                                            fill='white', font=('Helvetica', 14, 'bold'),
                                            text=self._stamina_text())

        self.status_label = tk.Label(root, text="", fg='white', bg='black', font=('Helvetica', 12))
        self.status_label.pack(pady=2)

        self.root.bind('1', self.decrease_stamina)
        self.root.bind('2', self.increase_stamina)
        self.root.bind('3', self.reset_stamina)

        for key in self.effect_keys:
            self.root.bind(f'<KeyPress-{key}>', self.effect_key_press)
            self.root.bind(f'<KeyRelease-{key}>', self.effect_key_release)

        # New: backtick hold tracking and reset handler
        self.backtick_held = False
        self.root.bind('<KeyPress-`>', self.backtick_press)
        self.root.bind('<KeyRelease-`>', self.backtick_release)

        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        self.held_keys = set()
        self.effects_continuous_decrease = {k: False for k in self.effect_keys}

        self.click_times = {k: [] for k in self.effect_keys}

        self.update_loop_interval = 50
        self.update_loop()

    def start_move(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_move(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _stamina_text(self):
        return f"Stamina: {self.current_stamina:.1f} / {self.effective_max_stamina():.1f}"

    def effective_max_stamina(self):
        total = self.base_max_stamina
        for k, eff in self.effects.items():
            if k == '7':
                continue
            total -= eff['value']
        return max(total, 0.0)

    def update_stamina_bar(self):
        max_stam = self.effective_max_stamina()
        if self.current_stamina > max_stam:
            self.current_stamina = max_stam
        width = (self.current_stamina / max_stam) * self.bar_length if max_stam > 0 else 0

        self.canvas.coords(self.stamina_bar_front,
                           self.bar_x_start, self.bar_y_start,
                           self.bar_x_start + width, self.bar_y_end)

        pct = self.current_stamina / max_stam if max_stam > 0 else 0
        color = "green" if pct > 0.6 else "yellow" if pct > 0.3 else "red"
        self.canvas.itemconfig(self.stamina_bar_front, fill=color)

        bar_height = 6
        gap = 2
        y_start = self.bar_y_start - bar_height - gap
        for i, key in enumerate(self.effect_keys):
            val = self.effects[key]['value']
            length = min(max(val, 0.0), self.base_max_stamina)
            w = (length / self.base_max_stamina) * self.bar_length
            y1 = y_start - i * (bar_height + gap)
            y2 = y1 + bar_height
            self.canvas.coords(self.effect_bars[key], self.bar_x_start, y1, self.bar_x_start + w, y2)

        self.canvas.itemconfig(self.text, text=self._stamina_text())

    def decrease_stamina(self, event=None):
        dec_amount = 0.5
        self.current_stamina = max(0, self.current_stamina - dec_amount)
        self.update_stamina_bar()

    def increase_stamina(self, event=None):
        inc_amount = 0.5
        max_stam = self.effective_max_stamina()
        self.current_stamina = min(max_stam, self.current_stamina + inc_amount)
        self.update_stamina_bar()

    def reset_stamina(self, event=None):
        self.current_stamina = self.effective_max_stamina()
        self.update_stamina_bar()

    # New backtick press/release handlers
    def backtick_press(self, event):
        self.backtick_held = True

    def backtick_release(self, event):
        if not self.held_keys:
            self.reset_last_effect()
        self.backtick_held = False

    def effect_key_press(self, event):
        key = event.keysym
        if key not in self.effect_keys:
            return

        if self.backtick_held:
            # Reset this effect immediately
            if self.effects[key]['value'] > 0:
                self.effects[key]['value'] = 0.0
                if key == '7':  # poison reset timers
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

        # Normal effect key handling:
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

    def change_effect_value(self, key, delta):
        old_val = self.effects[key]['value']
        new_val = min(max(old_val + delta, 0.0), self.base_max_stamina)
        self.effects[key]['value'] = new_val

        max_stam = self.effective_max_stamina()
        if self.current_stamina > max_stam:
            self.current_stamina = max_stam

    def show_effect_status(self, key, msg):
        self.status_label.config(text=msg)
        self.root.after(3000, self.clear_status)

    def clear_status(self):
        self.status_label.config(text="")

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

    def update_loop(self):
        now = time.time()
        inc_rate = 0.5 * (self.update_loop_interval / 1000) * 10

        for key in list(self.held_keys):
            self.change_effect_value(key, inc_rate)

        dec_rate = 0.5 * (self.update_loop_interval / 1000) * 5
        for key, continuous in self.effects_continuous_decrease.items():
            if continuous:
                self.change_effect_value(key, -dec_rate)

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


if __name__ == "__main__":
    root = tk.Tk()
    app = StaminaBarApp(root)
    root.mainloop()
