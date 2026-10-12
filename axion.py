import math
import queue
import threading
import time
import tkinter as tk
import webbrowser
from urllib.parse import urlencode


BG = "#000000"
TEXT = "#053a21"
MUTED = "#c4cecc"
CYAN = "#e5e5e5"
MONO = "Courier New"


class JarvisInterface(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("JARVIS")
        self.geometry("760x560")
        self.configure(bg=BG)

        self.status_text = tk.StringVar(value="SYSTEM ONLINE")
        self.clock_text = tk.StringVar()
        self._voice_results = queue.Queue()
        self._listening = False

        self._build_ui()
        self._update_clock()
        self._pulse_logo()
        self.after(100, self._poll_voice_results)

    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)

        self.logo_frame = tk.Frame(root, bg=BG)
        self.logo_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.canvas = tk.Canvas(self.logo_frame, width=260, height=260, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.configure(cursor="hand2")
        self.canvas.bind("<Button-1>", self._handle_core_tap)
        self._draw_logo()

        tk.Label(
            self.logo_frame,
            text="JARVIS",
            fg=TEXT,
            bg=BG,
            font=("Helvetica", 28, "bold"),
            pady=8,
        ).pack()

        self.search_var = tk.StringVar(value="Search Google...")
        search_row = tk.Frame(self.logo_frame, bg=BG)
        search_row.pack(pady=(0, 12))
        search = tk.Entry(
            search_row,
            textvariable=self.search_var,
            width=29,
            bg="#102427",
            fg=TEXT,
            insertbackground=CYAN,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#8deee3",
            highlightcolor=CYAN,
            font=(MONO, 10),
        )
        search.pack(side="left", ipady=6)
        tk.Button(
            search_row,
            text="SEARCH",
            command=self._run_search,
            bg="#102427",
            fg=CYAN,
            activebackground="#173a3d",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=6,
            font=(MONO, 9, "bold"),
        ).pack(side="left", padx=(6, 0))
        search.bind("<FocusIn>", lambda event: self._clear_search_placeholder(search))
        search.bind("<Return>", lambda event: self._run_search())
        search.bind("<FocusOut>", lambda event: self._restore_search_placeholder(search))

        tk.Label(
            self.logo_frame,
            text="PERSONAL INTELLIGENCE SYSTEM",
            fg=MUTED,
            bg=BG,
            font=(MONO, 9),
        ).pack(pady=(0, 12))

        tk.Label(
            self.logo_frame,
            textvariable=self.status_text,
            fg=CYAN,
            bg=BG,
            font=(MONO, 10, "bold"),
        ).pack()

        tk.Label(
            self.logo_frame,
            textvariable=self.clock_text,
            fg=MUTED,
            bg=BG,
            font=(MONO, 9),
        ).pack(pady=(6, 0))

    def _draw_logo(self):
        self.canvas.delete("all")
        cx, cy = 130, 130
        pulse = getattr(self, "pulse", 0)

        for radius, color in ((110 + pulse, "#173a3d"), (84 + pulse, "#295a5d"), (58, CYAN)):
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline=color, width=1.5)

        self.canvas.create_text(cx, cy - 10, text="J", fill=CYAN, font=(MONO, 93, "bold"))
        self.canvas.create_text(cx, cy + 62, text="◉", fill=CYAN, font=(MONO, 18, "bold"))

    def _pulse_logo(self):
        self.pulse = (getattr(self, "pulse", 0) + 1) % 12
        self._draw_logo()
        self.after(180, self._pulse_logo)

    def _handle_core_tap(self, event):
        if math.hypot(event.x - 130, event.y - 130) <= 58:
            self._start_voice_input()

    def _start_voice_input(self):
        if self._listening:
            return
        self._listening = True
        self.status_text.set("LISTENING...")
        threading.Thread(target=self._capture_voice, daemon=True).start()

    def _capture_voice(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self._voice_results.put(("status", "INSTALL SPEECHRECOGNITION + PYAUDIO"))
            return

        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=10)
            self._voice_results.put(("text", recognizer.recognize_google(audio)))
        except sr.WaitTimeoutError:
            self._voice_results.put(("status", "NO SPEECH DETECTED"))
        except sr.UnknownValueError:
            self._voice_results.put(("status", "COULD NOT UNDERSTAND"))
        except sr.RequestError:
            self._voice_results.put(("status", "VOICE SERVICE UNAVAILABLE"))
        except (OSError, AttributeError):
            self._voice_results.put(("status", "MICROPHONE UNAVAILABLE"))

    def _poll_voice_results(self):
        try:
            result_type, result = self._voice_results.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_voice_results)
            return

        self._listening = False
        if result_type == "text":
            self.search_var.set(result)
            self._run_search()
        else:
            self.status_text.set(result)
        self.after(100, self._poll_voice_results)

    def _update_clock(self):
        self.clock_text.set(time.strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)

    def _clear_search_placeholder(self, entry):
        if entry.get() == "Search Google...":
            entry.delete(0, tk.END)

    def _restore_search_placeholder(self, entry):
        if entry.get().strip() == "":
            entry.delete(0, tk.END)
            entry.insert(0, "Search Google...")

    def _run_search(self):
        query = self.search_var.get().strip()
        if not query or query == "Search Google...":
            return
        search_url = "https://www.google.com/search?" + urlencode({"q": query})
        if webbrowser.open_new_tab(search_url):
            self.status_text.set(f"GOOGLE: {query.upper()}")
        else:
            self.status_text.set("COULD NOT OPEN BROWSER")


if __name__ == "__main__":
    app = JarvisInterface()
    app.mainloop()



    