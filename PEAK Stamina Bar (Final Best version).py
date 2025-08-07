import tkinter as tk
import time
from tkinter import ttk

class StaminaBarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PEAK Stamina Bar")

        self.root.overrideredirect(True)

        transparent_color = "black"
        self.root.config(bg=transparent_color)
        self.root.wm_attributes('-transparentcolor', transparent_color)
        self.root.wm_attributes("-topmost", True)

        self.base_max_stamina = 100.0
        self.current_stamina = 100.0
        self.current_extra_stamina = 0.0

        # Initialize stamina regen and auto decrease rates (per second)
        self.stamina_regen_rate = 10.0
        self.stamina_auto_decrease_rate = 5.0

        self.effects = {
            "4": {"name": "Weight", "color": "brown", "value": 0.0, "continuous_decrease": False},
            "5": {"name": "Hunger", "color": "yellow", "value": 0.0, "continuous_decrease": False},
            "6": {"name": "Damage", "color": "red", "value": 0.0, "continuous_decrease": False},
            "7": {"name": "Poison", "color": "purple", "value": 0.0, "continuous_decrease": False,
                  "poison_timer": 30.0, "poison_active": False, "poison_decrement_interval": 10.0, "last_poison_tick": 0.0},
            "8": {"name": "Cold", "color": "cyan", "value": 0.0, "continuous_decrease": False},
            "9": {"name": "Heat", "color": "dark red", "value": 0.0, "continuous_decrease": False},
            "0": {"name": "Drowsy", "color": "pink", "value": 0.0, "continuous_decrease": False},
            "minus": {"name": "Curse", "color": "purple", "value": 0.0, "continuous_decrease": False}
        }
        self.effect_keys = ['4', '5', '6', '7', '8', '9', '0', 'minus']

        self.canvas_width = 540
        self.canvas_height = 150
        self.bar_x_start = 15
        self.bar_x_end = 465
        self.bar_y_start = 60
        self.bar_y_end = 90
        self.bar_length = self.bar_x_end - self.bar_x_start
        self.bar_height = self.bar_y_end - self.bar_y_start

        self.canvas = tk.Canvas(root, width=self.canvas_width, height=self.canvas_height,
                                bg=transparent_color, highlightthickness=0)
        self.canvas.pack()

        self.stamina_bar_back = self.canvas.create_rectangle(
            self.bar_x_start, self.bar_y_start,
            self.bar_x_end, self.bar_y_end,
            fill='grey', outline='white'
        )

        self.stamina_bar_front = self.canvas.create_rectangle(
            self.bar_x_start, self.bar_y_start,
            self.bar_x_end, self.bar_y_end,
            fill='green', outline=''
        )

        self.extra_bar_y_start = self.bar_y_end + 15
        self.extra_bar_y_end = self.extra_bar_y_start + self.bar_height

        self.extra_stamina_bar_back = self.canvas.create_rectangle(
            self.bar_x_start, self.extra_bar_y_start,
            self.bar_x_end, self.extra_bar_y_end,
            fill='', outline=''
        )
        self.extra_stamina_bar_front = self.canvas.create_rectangle(
            self.bar_x_start, self.extra_bar_y_start,
            self.bar_x_end, self.extra_bar_y_end,
            fill='', outline=''
        )

        self.effect_bars = {}
        effect_bar_height = self.bar_height / len(self.effect_keys)
        for i, key in enumerate(self.effect_keys):
            y1 = self.bar_y_start + i * effect_bar_height
            y2 = y1 + effect_bar_height
            rect_id = self.canvas.create_rectangle(
                self.bar_x_start, y1, self.bar_x_start, y2,
                fill=self.effects[key]['color'], outline=''
            )
            self.effect_bars[key] = rect_id

        self.text = self.canvas.create_text(
            (self.bar_x_start + self.bar_x_end) // 2,
            self.bar_y_start + self.bar_height / 2,
            fill='white', font=('Helvetica', 24, 'bold'),
            text=self._stamina_text())
        self.canvas.tag_raise(self.text)

        self.extra_text = self.canvas.create_text(
            (self.bar_x_start + self.bar_x_end) // 2,
            self.extra_bar_y_start + self.bar_height / 2,
            fill='',
            font=('Helvetica', 20, 'bold'),
            text=""
        )
        self.canvas.tag_raise(self.extra_text)

        self.hunger_label_text = self.canvas.create_text(
            self.bar_x_end + 20,
            self.bar_y_start + 10,
            fill='white', font=('Helvetica', 11, 'bold'),
            text="Hunger-Time:",
            anchor='w'
        )
        self.hunger_time_text = self.canvas.create_text(
            self.bar_x_end + 20,
            self.bar_y_start + 30,
            fill='white', font=('Helvetica', 11, 'normal'),
            text="120s",
            anchor='w'
        )

        self.status_label = tk.Label(root, text="", fg='white', bg=transparent_color, font=('Helvetica', 16))
        self.status_label.pack(pady=5)

        # Keybindings without 'i' key bind
        self.root.bind('1', self.handle_one_key)
        self.root.bind('2', self.increase_stamina)
        self.root.bind('3', self.reset_stamina)
        self.root.bind('q', self.increase_extra_stamina)
        self.root.bind('e', self.handle_e_key)
        self.root.bind('r', self.reset_extra_stamina)
        self.root.bind('w', self.toggle_main_stamina_regen)
        self.root.bind('o', self.open_effect_adjuster)

        for key in self.effect_keys:
            self.root.bind(f'<KeyPress-{key}>', self.effect_key_press)
            self.root.bind(f'<KeyRelease-{key}>', self.effect_key_release)

        self.root.bind('<KeyPress-equal>', self.toggle_hunger_auto)
        self.root.bind('<KeyRelease-equal>', self.equal_release)
        self.root.bind('<KeyPress-bracketright>', self.reset_hunger_timer)

        self.backtick_held = False
        self.root.bind('<KeyPress-`>', self.backtick_press)
        self.root.bind('<KeyRelease-`>', self.backtick_release)

        self.main_stamina_regen_enabled = True

        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)

        self.held_keys = set()
        self.effects_continuous_decrease = {k: False for k in self.effect_keys}
        self.click_times = {k: [] for k in self.effect_keys}

        self.hunger_auto_enabled = True
        self.hunger_auto_interval = 120.0
        self.hunger_auto_timer = self.hunger_auto_interval
        self.equal_held = False

        self.double_tap_times = {'1': [], 'e': []}
        self.auto_decrease_main = False
        self.auto_decrease_extra = False

        self.update_loop_interval = 50
        self.update_loop()

    def _stamina_text(self):
        return f"Stamina {self.current_stamina:.1f}"

    def _extra_stamina_text(self):
        return f"Extra Stamina {self.current_extra_stamina:.1f}"

    def effective_max_stamina(self):
        total = self.base_max_stamina
        for k, eff in self.effects.items():
            total -= eff['value']
        return max(total, 0.0)

    def update_hunger_time_text(self):
        if self.hunger_auto_enabled:
            sec_left = int(max(0, self.hunger_auto_timer))
            self.canvas.itemconfig(self.hunger_time_text, text=f"{sec_left}s")
        else:
            self.canvas.itemconfig(self.hunger_time_text, text="Paused")

    def update_stamina_bar(self):
        max_stam = self.effective_max_stamina()
        self.current_stamina = max(0.0, min(self.current_stamina, max_stam))
        self.current_extra_stamina = max(0.0, min(self.current_extra_stamina, 100.0))

        bar_width = (self.current_stamina / max_stam) * self.bar_length if max_stam > 0 else 0
        extra_bar_width = (self.current_extra_stamina / 100.0) * self.bar_length

        self.canvas.coords(self.stamina_bar_front, self.bar_x_start, self.bar_y_start,
                           self.bar_x_start + bar_width, self.bar_y_end)
        self.canvas.itemconfig(self.stamina_bar_front, fill="green")

        if self.current_extra_stamina > 0:
            self.canvas.coords(self.extra_stamina_bar_back,
                               self.bar_x_start, self.extra_bar_y_start,
                               self.bar_x_end, self.extra_bar_y_end)
            self.canvas.itemconfig(self.extra_stamina_bar_back, fill='grey', outline='white')
            self.canvas.coords(self.extra_stamina_bar_front,
                               self.bar_x_start, self.extra_bar_y_start,
                               self.bar_x_start + extra_bar_width, self.extra_bar_y_end)
            self.canvas.itemconfig(self.extra_stamina_bar_front, fill='light green')
            self.canvas.itemconfig(self.extra_text, fill='white', text=self._extra_stamina_text())
        else:
            self.canvas.itemconfig(self.extra_stamina_bar_back, fill='', outline='')
            self.canvas.itemconfig(self.extra_stamina_bar_front, fill='', outline='')
            self.canvas.itemconfig(self.extra_text, fill='', text='')

        effect_bar_height = self.bar_height / len(self.effect_keys)
        for i, key in enumerate(self.effect_keys):
            val = self.effects[key]['value']
            length_ratio = max(0.0, min(val / self.base_max_stamina, 1.0))
            y1 = self.bar_y_start + i * effect_bar_height
            y2 = y1 + effect_bar_height
            if self.current_stamina > 0:
                effect_width = bar_width * length_ratio
                x1 = self.bar_x_start
                x2 = x1 + effect_width
            else:
                x1 = self.bar_x_end
                effect_width = self.bar_length * length_ratio
                x2 = x1 + effect_width
            self.canvas.coords(self.effect_bars[key], x1, y1, x2, y2)

        self.update_hunger_time_text()
        self.canvas.tag_raise(self.text)
        self.canvas.itemconfig(self.text, text=self._stamina_text())

    def open_effect_adjuster(self, event=None):
        if hasattr(self, 'effect_win') and self.effect_win.winfo_exists():
            self.effect_win.lift()
            return

        self.effect_win = tk.Toplevel(self.root)
        self.effect_win.overrideredirect(True)
        self.effect_win.config(bg='black')
        self.effect_win.wm_attributes('-transparentcolor', 'black')
        self.effect_win.wm_attributes('-topmost', True)

        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        self.effect_win.geometry(f"320x210+{main_x + 100}+{main_y + 100}")

        def start_move(event):
            self.effect_win._drag_start_x = event.x
            self.effect_win._drag_start_y = event.y

        def do_move(event):
            x = self.effect_win.winfo_x() + event.x - self.effect_win._drag_start_x
            y = self.effect_win.winfo_y() + event.y - self.effect_win._drag_start_y
            self.effect_win.geometry(f"+{x}+{y}")

        self.effect_win.bind("<ButtonPress-1>", start_move)
        self.effect_win.bind("<B1-Motion>", do_move)

        options = list(self.effects.keys()) + ['main_stamina', 'extra_stamina', 'stamina_regen_rate', 'stamina_auto_decrease_rate']
        option_names = [
            self.effects[k]['name'] if k in self.effects else {
                'main_stamina': 'Main Stamina',
                'extra_stamina': 'Extra Stamina',
                'stamina_regen_rate': 'Stamina Regeneration Rate',
                'stamina_auto_decrease_rate': 'Stamina Auto-Decrease Rate'
            }[k]
            for k in options
        ]

        self.selected_option = tk.StringVar(value=options[0])
        combobox = ttk.Combobox(self.effect_win, values=option_names, state='readonly')
        combobox.current(0)
        combobox.pack(pady=10, padx=10, fill='x')

        def on_select(event):
            idx = combobox.current()
            self.selected_option.set(options[idx])
        combobox.bind("<<ComboboxSelected>>", on_select)

        amount_frame = tk.Frame(self.effect_win, bg='black')
        amount_frame.pack(pady=(5, 10))

        tk.Label(amount_frame, text="Amount:", fg='white', bg='black').pack(side='left', padx=(0, 5))
        amount_var = tk.StringVar(value="1.0")
        amount_entry = tk.Entry(amount_frame, textvariable=amount_var, width=10)
        amount_entry.pack(side='left')

        btn_frame = tk.Frame(self.effect_win, bg='black')
        btn_frame.pack(pady=10)

        def adjust(delta_sign):
            try:
                val = float(amount_var.get())
                if val < 0:
                    val = abs(val)
            except ValueError:
                val = 1.0

            delta = val * delta_sign
            key = self.selected_option.get()

            if key == 'main_stamina':
                max_stam = self.effective_max_stamina()
                new_val = min(max(self.current_stamina + delta, 0), max_stam)
                self.current_stamina = new_val
            elif key == 'extra_stamina':
                new_val = min(max(self.current_extra_stamina + delta, 0), 100.0)
                self.current_extra_stamina = new_val
            elif key == 'stamina_regen_rate':
                self.stamina_regen_rate = max(self.stamina_regen_rate + delta, 0.0)
                self.show_effect_status('', f"Stamina Regen Rate set to {self.stamina_regen_rate:.2f}")
            elif key == 'stamina_auto_decrease_rate':
                self.stamina_auto_decrease_rate = max(self.stamina_auto_decrease_rate + delta, 0.0)
                self.show_effect_status('', f"Stamina Auto-Decrease Rate set to {self.stamina_auto_decrease_rate:.2f}")
            else:
                old_val = self.effects[key]['value']
                new_val = min(max(old_val + delta, 0), self.base_max_stamina)
                self.effects[key]['value'] = new_val
                max_stam = self.effective_max_stamina()
                if self.current_stamina > max_stam:
                    self.current_stamina = max_stam
            self.update_stamina_bar()

        inc_btn = tk.Button(btn_frame, text="Increase", command=lambda: adjust(1.0))
        inc_btn.pack(side='left', padx=10)
        dec_btn = tk.Button(btn_frame, text="Decrease", command=lambda: adjust(-1.0))
        dec_btn.pack(side='left', padx=10)

        close_btn = tk.Button(self.effect_win, text="Close", command=self.effect_win.destroy)
        close_btn.pack(pady=5)

    def process_double_tap(self, key):
        now = time.time()
        times = self.double_tap_times[key]
        times.append(now)
        if len(times) > 2:
            times.pop(0)
        if len(times) == 2 and (times[1] - times[0] <= 0.5):
            if key == '1':
                self.auto_decrease_main = not self.auto_decrease_main
                msg = "Auto decreasing main stamina started" if self.auto_decrease_main else "Auto decreasing main stamina stopped"
                self.show_effect_status('', msg)
            elif key == 'e':
                self.auto_decrease_extra = not self.auto_decrease_extra
                msg = "Auto decreasing extra stamina started" if self.auto_decrease_extra else "Auto decreasing extra stamina stopped"
                self.show_effect_status('', msg)

    def stop_auto_decreases(self):
        if self.auto_decrease_main or self.auto_decrease_extra:
            self.auto_decrease_main = False
            self.auto_decrease_extra = False
            self.show_effect_status('', "Auto decreasing stopped")

    def handle_one_key(self, event=None):
        self.process_double_tap('1')
        if not self.auto_decrease_main:
            self.current_stamina = max(0, self.current_stamina - 0.5)
            self.update_stamina_bar()

    def handle_e_key(self, event=None):
        self.process_double_tap('e')
        if not self.auto_decrease_extra:
            self.current_extra_stamina = max(0, self.current_extra_stamina - 0.5)
            self.update_stamina_bar()

    def increase_extra_stamina(self, event=None):
        self.current_extra_stamina = min(self.current_extra_stamina + 5, 100.0)
        self.update_stamina_bar()

    def reset_extra_stamina(self, event=None):
        self.current_extra_stamina = 100.0
        self.update_stamina_bar()
        self.show_effect_status('', "Extra stamina reset to max")

    def decrease_stamina(self, event=None):
        dec_amount = 0.5
        self.current_stamina = max(0.0, self.current_stamina - dec_amount)
        self.update_stamina_bar()

    def increase_stamina(self, event=None):
        inc_amount = 0.5
        max_stam = self.effective_max_stamina()
        self.current_stamina = min(max_stam, self.current_stamina + inc_amount)
        self.update_stamina_bar()

    def reset_stamina(self, event=None):
        self.current_stamina = self.effective_max_stamina()
        self.update_stamina_bar()

    def toggle_hunger_auto(self, event=None):
        self.hunger_auto_enabled = not self.hunger_auto_enabled
        status = "paused" if not self.hunger_auto_enabled else "resumed"
        self.show_effect_status('', f"Hunger auto-increase {status}")
        self.equal_held = True

    def equal_release(self, event=None):
        self.equal_held = False

    def reset_hunger_timer(self, event=None):
        self.hunger_auto_timer = self.hunger_auto_interval
        self.show_effect_status('', "Hunger timer reset to full")

    def backtick_press(self, event):
        self.backtick_held = True

    def backtick_release(self, event):
        if not self.held_keys:
            self.reset_last_effect()
        self.backtick_held = False

    def effect_key_press(self, event):
        key = event.keysym
        if key != '1' and key != 'e':
            self.stop_auto_decreases()

        if key not in self.effect_keys:
            return

        if key != 'equal':
            self.equal_held = False

        if self.backtick_held:
            if self.effects[key]['value'] > 0:
                self.effects[key]['value'] = 0.0
                if key == '7':
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
        if key == 'equal':
            self.equal_held = False

    def detect_click_type(self, timestamps):
        threshold = 0.4
        if len(timestamps) == 1:
            return 1
        elif len(timestamps) == 2:
            return 2 if timestamps[-1] - timestamps[-2] <= threshold else 1
        elif len(timestamps) == 3:
            t1, t2, t3 = timestamps[-3], timestamps[-2], timestamps[-1]
            if t3 - t1 <= threshold * 2:
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

        if self.hunger_auto_enabled:
            self.hunger_auto_timer -= self.update_loop_interval / 1000
            if self.hunger_auto_timer <= 0:
                self.change_effect_value('5', 2.0)
                self.hunger_auto_timer = self.hunger_auto_interval
                self.show_effect_status('', "Hunger increased by +2.0 automatically")

        if self.auto_decrease_main:
            decay_rate = self.stamina_auto_decrease_rate * (self.update_loop_interval / 1000)
            self.current_stamina = max(0, self.current_stamina - decay_rate)
        else:
            if self.main_stamina_regen_enabled:
                if self.current_stamina < self.effective_max_stamina():
                    regen_rate = self.stamina_regen_rate * (self.update_loop_interval / 1000)
                    self.current_stamina = min(self.effective_max_stamina(), self.current_stamina + regen_rate)

        if self.auto_decrease_extra:
            decay_rate = 0.5 * (self.update_loop_interval / 1000) * 10
            self.current_extra_stamina = max(0, self.current_extra_stamina - decay_rate)

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

    def toggle_main_stamina_regen(self, event=None):
        self.main_stamina_regen_enabled = not self.main_stamina_regen_enabled
        status = "Main stamina regeneration paused" if not self.main_stamina_regen_enabled else "Main stamina regeneration resumed"
        self.show_effect_status('', status)

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
