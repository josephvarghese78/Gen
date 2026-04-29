import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import requests
import sqlite3
import uuid
import shutil
import os
import json
import random
from datetime import datetime
import inspect
import config as cfg
from custom import api_requests

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ══════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (light theme)
# ══════════════════════════════════════════════════════════════
BG          = "#f0f4f8"   # soft light grey background
BG2         = "#ffffff"   # white panel
CARD        = "#1e3a5f"   # dark navy card fill for header
ACCENT      = "#c0392b"   # rich red accent
ACCENT2     = "#7c4daa"   # soft purple accent
TEXT        = "#1a1a2e"   # dark text for readability
TEXT_DIM    = "#5a6a7a"   # muted dark-grey text
GREEN       = "#1a7a4a"   # dark green for success
RED         = "#c0392b"   # rich red for failure
YELLOW      = "#b85c00"   # dark amber for warnings
WHITE       = "#ffffff"
FONT_HDR    = ("Segoe UI", 20, "bold")
FONT_SUB    = ("Segoe UI", 9)
FONT_LBL    = ("Segoe UI", 9, "bold")
FONT_VAL    = ("Segoe UI", 14, "bold")
FONT_MONO   = ("Consolas", 9)

# ══════════════════════════════════════════════════════════════
#  LOGGING HELPER
# ══════════════════════════════════════════════════════════════
def log_performance(test_name,
                    thread_name, iteration, start_time, end_time,
                    samples_started, samples_completed, active_threads,think_time,
                    response_time, error_status, error_percent, response_status_code, response):
    db_conn = sqlite3.connect(f"./db/{cfg.db_filename}")
    db_cursor = db_conn.cursor()

    db_cursor.execute("""
            INSERT INTO performance (suite_name,
            test_name, max_threads, thread_name, iteration, start_time,
            end_time, samples_started, samples_completed, active_threads,
            think_time, response_time, error_status, error_percent, response_status_code,
            response ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?,?,?,?,?)
            """,
                      (cfg.suite_id, test_name, cfg.users, thread_name, iteration, start_time, end_time,
                       samples_started, samples_completed, active_threads,
                       think_time, response_time, error_status, error_percent, response_status_code, response))

    db_conn.commit()
    db_conn.close()



def task_propotion(lst, users, weights):
    total = sum(weights)
    w_users=int(round(random.choice([.2,.25,.3,.35,.4,.45,.5,.55])))
    percentages = [round((w / total) * (users+w_users), 0) for w in weights]
    d_list = []

    for i in range(len(lst)):
        p = percentages[i]
        for j in range(int(p)):
            d_list.append(lst[i])

    #if len(d_list) > users:
    #    d_list = d_list[:users]

    while len(d_list) < users:
        d_list.append(random.choices(lst, weights)[0])

    random.shuffle(d_list)
    return d_list

# ══════════════════════════════════════════════════════════════
#  WORKER THREAD
# ══════════════════════════════════════════════════════════════
class UserThread:
    def __init__(self, thread_name, thread_task, log_fn):
        self.thread_name = thread_name
        self.thread_task=thread_task
        self.log = log_fn

    def run(self):
        i = 0
        user_session = requests.session()
        while (not cfg.stop_requested) and \
              (time.time() - cfg.test_start_time) < (cfg.runfor * 60):
            if cfg.error_percent >= cfg.error_threshold:
                self.log(f"[{self.thread_name}] ⛔ Error threshold reached, stopping.", "warn")
                break
            i += 1
            cfg.samples_started += 1

            (resp, status_code, error_flag, think_time, test_name,
             start_time, start_time_pc, end_time, end_time_pc,
             response_time) = self.api_request_main(user_session, self.thread_task)

            cfg.samples_completed += 1
            if error_flag in cfg.error_flags:
                cfg.current_errors += 1
                self.log(f"❌  [{self.thread_name}]  {test_name}  │  {status_code}  │  {response_time:.2f} ms", "err")
            else:
                cfg.total_response_time += (response_time/1000)
                cfg.avg = cfg.total_response_time / cfg.samples_completed if cfg.samples_completed > 0 else 0
                self.log(f"✅  [{self.thread_name}]  {test_name}  │  {status_code}  │  {response_time:.2f} ms", "ok")

            cfg.error_percent = (cfg.current_errors / cfg.samples_started) * 100

            log_performance(test_name, self.thread_name, i,
                            start_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                            end_time.strftime("%Y-%m-%d %H:%M:%S.%f"),
                            cfg.samples_started,
                            cfg.samples_completed,
                            cfg.running_users,
                            think_time * 1000,
                            response_time,
                            error_flag,
                            cfg.error_percent,
                            status_code,
                            str(resp))

        if not cfg.stop_requested and \
           (time.time() - cfg.test_start_time) >= (cfg.runfor * 60):
            cfg.running_users -= 1

    def api_request_main(self, user_session, f):
        tt = random.choice(cfg.think_time)
        start_time = None
        start_time_pc = None
        end_time = None
        end_time_pc = None
        response_time = None
        test_name = None
        try:

            time.sleep(tt)
            start_time = datetime.now()
            start_time_pc = time.perf_counter()

            resp, test_name = f(user_session)

            end_time = datetime.now()
            end_time_pc = time.perf_counter()
            response_time = (end_time_pc - start_time_pc) * 1000

            if resp is not None:
                try:
                    resp_content = resp.json()
                except ValueError:
                    resp_content = resp.text

                status_code = resp.status_code
                error_flag = 0 if resp.status_code in cfg.valid_status_codes + cfg.ignore_status_codes else 1

                status_code = resp.status_code
                error_flag = ""
                if resp.status_code in cfg.valid_status_codes:
                    error_flag = "P"
                elif resp.status_code in cfg.ignore_status_codes:
                    error_flag = "W"
                else:
                    error_flag = "F"

                return resp_content, status_code, error_flag, tt, test_name, start_time, start_time_pc, end_time, end_time_pc, response_time
            else:
                return "None", "0", "W", tt, test_name, start_time, start_time_pc, end_time, end_time_pc, response_time

        except Exception as e:
            print(e)
            return str(e), 0, 1, tt, test_name, start_time, start_time_pc, end_time, end_time_pc, response_time
            
            
# ══════════════════════════════════════════════════════════════
#  MAIN UI CLASS
# ══════════════════════════════════════════════════════════════
class BenchUI:
    def __init__(self, root):
        self.users=0
        self.root = root
        self.root.title("⚡ Performance Bench Test — Control Panel")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(1100, 720)
        self._stop_flag = False
        self._test_done_flag=False

        # ── Live chart history buffers ──────────────────────
        self._chart_time   = []
        self._chart_avg_rt = []
        self._chart_tps    = []
        self._chart_tpm    = []
        self._chart_eff    = []
        self._MAX_POINTS   = 120

        self._apply_ttk_theme()
        self._build_ui()

    # ── TTK custom style ───────────────────────────────────────
    def _apply_ttk_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        # general
        style.configure(".",
                         background=BG, foreground=TEXT,
                         fieldbackground=BG2, bordercolor=CARD,
                         troughcolor=BG2, selectbackground=ACCENT,
                         selectforeground=WHITE, font=FONT_SUB)

        # labelled frames
        style.configure("Card.TLabelframe",
                         background=BG2, relief="flat",
                         bordercolor=CARD, borderwidth=2)
        style.configure("Card.TLabelframe.Label",
                         background=BG2, foreground=ACCENT,
                         font=("Segoe UI", 10, "bold"))

        # entries
        style.configure("Dark.TEntry",
                         fieldbackground="#eef2f7", foreground=TEXT,
                         insertcolor=TEXT, bordercolor="#b0c4d8",
                         relief="flat", padding=5)
        style.map("Dark.TEntry",
                  bordercolor=[("focus", ACCENT)])

        # primary button
        style.configure("Start.TButton",
                         background="#1a7a4a", foreground=WHITE,
                         font=("Segoe UI", 10, "bold"),
                         padding=(14, 8), relief="flat", borderwidth=0)
        style.map("Start.TButton",
                  background=[("active", "#155e38"), ("disabled", "#a0c8b0")],
                  foreground=[("disabled", "#ffffff")])

        # stop button
        style.configure("Stop.TButton",
                         background=RED, foreground=WHITE,
                         font=("Segoe UI", 10, "bold"),
                         padding=(14, 8), relief="flat", borderwidth=0)
        style.map("Stop.TButton",
                  background=[("active", "#cc3344"), ("disabled", "#5a2a2a")],
                  foreground=[("disabled", "#888888")])

        # clear button
        style.configure("Clear.TButton",
                         background=ACCENT2, foreground=WHITE,
                         font=("Segoe UI", 10, "bold"),
                         padding=(14, 8), relief="flat", borderwidth=0)
        style.map("Clear.TButton",
                  background=[("active", "#6a44a3")])

        # progress bar
        style.configure("Accent.Horizontal.TProgressbar",
                         troughcolor=BG2, background=ACCENT,
                         bordercolor=BG2, lightcolor=ACCENT,
                         darkcolor=ACCENT, thickness=8)

    # ── Master layout ──────────────────────────────────────────
    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)

        # ── Header ────────────────────────────
        hdr = tk.Frame(self.root, bg=CARD, pady=14)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(0, weight=1)

        tk.Label(hdr, text="⚡  Performance Bench Test",
                 bg=CARD, fg=WHITE, font=FONT_HDR).grid(row=0, column=0)
        tk.Label(hdr,
                 text="Configure parameters, launch threads and monitor results in real time",
                 bg=CARD, fg="#a0bcd8", font=FONT_SUB).grid(row=1, column=0)

        # ── Params ────────────────────────────
        param_outer = ttk.LabelFrame(self.root, text="  ⚙  Test Configuration",
                                     style="Card.TLabelframe")
        param_outer.grid(row=1, column=0, sticky="ew", padx=16, pady=(12, 4))
        param_outer.columnconfigure((1, 3), weight=1)

        fields_left = [
            ("📁  Project Name",    "project_name",    cfg.project_name),
            ("👥  Start Users",     "users",           str(cfg.users)),
            ("🛑  Stop At Users",   "stop_at_user",    str(cfg.stop_at_user)),
            ("📈  User Step",       "user_step",       str(cfg.user_step)),
        ]
        fields_right = [
            ("⏱  Run For (min)",   "runfor",          str(cfg.runfor)),
            ("🚨  Error Threshold %", "error_threshold", str(cfg.error_threshold)),
            ("🚀  Ramp-up / User (s)", "rampup_per_user", str(cfg.rampup_per_user)),
            ("💤  Think Time (s)",  "think_time",      str(cfg.think_time)),
        ]

        self.vars = {}
        for r, (lbl, key, val) in enumerate(fields_left):
            self._param_row(param_outer, lbl, key, val, r, 0)
        for r, (lbl, key, val) in enumerate(fields_right):
            self._param_row(param_outer, lbl, key, val, r, 2)

        tk.Label(param_outer,
                 text="💡  Lists accepted for ramp-up & think time e.g.  [2, 4, 6, 8]",
                 bg=BG2, fg=TEXT_DIM, font=("Segoe UI", 8, "italic")
                 ).grid(row=5, column=0, columnspan=4, padx=8, pady=(2, 6), sticky="w")

        # ── Buttons ───────────────────────────
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.grid(row=2, column=0, pady=10)

        self.btn_start = ttk.Button(btn_frame, text="▶   Start Test",
                                    style="Start.TButton",
                                    command=self._start_test)
        self.btn_start.grid(row=0, column=0, padx=8)

        self.btn_stop = ttk.Button(btn_frame, text="⏹   Stop Test",
                                   style="Stop.TButton",
                                   command=self._stop_test,
                                   state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=8)

        ttk.Button(btn_frame, text="🗑   Clear",
                   style="Clear.TButton",
                   command=self._clear_log).grid(row=0, column=2, padx=8)

        # ── Progress bar ──────────────────────
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self.root,
                                             variable=self.progress_var,
                                             maximum=100,
                                             style="Accent.Horizontal.TProgressbar")
        self.progress_bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 6))

        self.progress_lbl = tk.Label(self.root, text="Ready to run",
                                     bg=BG, fg=TEXT_DIM, font=("Segoe UI", 8))
        self.progress_lbl.grid(row=4, column=0)

        # ── Status cards ──────────────────────
        cards_frame = tk.Frame(self.root, bg=BG)
        cards_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=6)
        for c in range(6):
            cards_frame.columnconfigure(c, weight=1)

        self.lbl_users     = self._card(cards_frame, "ACTIVE USERS",  "—",  GREEN,  0)
        self.lbl_samples   = self._card(cards_frame, "SAMPLES",       "—",  ACCENT2, 1)
        self.lbl_errors    = self._card(cards_frame, "ERRORS",        "—",  RED,    2)
        self.lbl_error_pct = self._card(cards_frame, "ERROR RATE",    "—",  YELLOW, 3)
        self.lbl_elapsed   = self._card(cards_frame, "ELAPSED",       "—",  WHITE,  4)
        self.lbl_metrics   = self._card(cards_frame, "AVG-A.TP-T.TP-EFF", "—", WHITE, 5)

        # ── Bottom split: Console (left) + Chart (right) ──────
        bottom = tk.Frame(self.root, bg=BG)
        bottom.grid(row=6, column=0, sticky="nsew", padx=16, pady=(4, 12))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)
        self.root.rowconfigure(6, weight=1)

        # ── Console ────────────────────────────────────────
        log_frame = ttk.LabelFrame(bottom, text="  📋  Console Output",
                                   style="Card.TLabelframe")
        log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.console = scrolledtext.ScrolledText(
            log_frame, height=16,
            bg="#ffffff", fg="#1a1a2e",
            font=FONT_MONO,
            insertbackground=TEXT,
            selectbackground="#b0c4d8",
            state="disabled",
            relief="flat", padx=10, pady=10,
            spacing1=4, spacing2=2, spacing3=6)
        self.console.pack(fill="both", expand=True, padx=2, pady=2)

        self.console.tag_config("ok",     foreground="#1a7a4a")
        self.console.tag_config("err",    foreground="#c0392b")
        self.console.tag_config("warn",   foreground="#b85c00")
        self.console.tag_config("info",   foreground="#1a3a6e")
        self.console.tag_config("muted",  foreground="#7a8a9a")
        self.console.tag_config("sep",    foreground="#7c4daa")

        # ── Live Chart ─────────────────────────────────────
        chart_frame = ttk.LabelFrame(bottom, text="  📈  Performance Monitor",
                                     style="Card.TLabelframe")
        chart_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)

        self._fig = Figure(figsize=(5, 6), dpi=88, facecolor="#f8fafc")
        self._fig.subplots_adjust(hspace=0.55, top=0.95, bottom=0.08,
                                  left=0.18, right=0.97)

        self._ax_rt  = self._fig.add_subplot(4, 1, 1)
        self._ax_tps = self._fig.add_subplot(4, 1, 2)
        self._ax_tpm = self._fig.add_subplot(4, 1, 3)
        self._ax_eff = self._fig.add_subplot(4, 1, 4)

        self._init_chart_axes()

        self._canvas = FigureCanvasTkAgg(self._fig, master=chart_frame)
        self._canvas.draw()
        self._canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    # ── Helper: parameter row ──────────────────────────────────
    def _param_row(self, parent, label, key, default, row, col_offset):
        tk.Label(parent, text=label, bg=BG2, fg=TEXT,
                 font=FONT_LBL, anchor="w"
                 ).grid(row=row, column=col_offset,   sticky="w", padx=(12, 4), pady=5)
        var = tk.StringVar(value=default)
        self.vars[key] = var
        e = ttk.Entry(parent, textvariable=var, width=22, style="Dark.TEntry")
        e.grid(row=row, column=col_offset + 1, sticky="ew", padx=(0, 16), pady=5)

    # ── Helper: status card ────────────────────────────────────
    def _card(self, parent, title, init, color, col):
        frame = tk.Frame(parent, bg=CARD, padx=10, pady=8,
                         highlightbackground=color, highlightthickness=1)
        frame.grid(row=0, column=col, sticky="ew", padx=4)
        tk.Label(frame, text=title, bg=CARD, fg="#a0bcd8",
                 font=("Segoe UI", 7, "bold")).pack()
        var = tk.StringVar(value=init)
        tk.Label(frame, textvariable=var, bg=CARD, fg=color,
                 font=FONT_VAL).pack()
        return var

    # ── Console log ───────────────────────────────────────────
    def _log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console.configure(state="normal")
        self.console.insert("end", f"  {ts}  ", "muted")
        self.console.insert("end", f"{msg}\n", tag)
        self.console.see("end")
        self.console.configure(state="disabled")

    def _clear_log(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self._test_done_flag=False
        self._stop_flag=False
        cfg.avg=0
        cfg.total_response_time=0
        cfg.samples_started=0
        cfg.samples_completed=0
        cfg.running_users=0
        cfg.current_errors=0
        cfg.error_percent=0
        cfg.el=0
        cfg.stop_requested=False
        self.users = 0
        # reset chart buffers
        self._chart_time=[]; self._chart_avg_rt=[]; self._chart_tps=[]
        self._chart_tpm=[]; self._chart_eff=[]
        for ax in (self._ax_rt, self._ax_tps, self._ax_tpm, self._ax_eff):
            ax.cla()
        self._init_chart_axes()
        self._canvas.draw_idle()
        self.root.title("⚡ Performance Bench Test — Control Panel")

    # ── Parameter parsing ─────────────────────────────────────
    def _apply_params(self):
        try:
            cfg.project_name    = self.vars["project_name"].get().strip() or "MyProject"
            cfg.users           = int(self.vars["users"].get())
            cfg.stop_at_user    = int(self.vars["stop_at_user"].get())
            cfg.user_step       = int(self.vars["user_step"].get())
            cfg.runfor          = float(self.vars["runfor"].get())
            cfg.error_threshold = float(self.vars["error_threshold"].get())
            cfg.rampup_per_user = self._parse_num_or_list(self.vars["rampup_per_user"].get())
            cfg.think_time      = self._parse_num_or_list(self.vars["think_time"].get())
            return True
        except Exception as e:
            messagebox.showerror("Parameter Error", str(e))
            return False

    @staticmethod
    def _parse_num_or_list(raw):
        raw = raw.strip()
        if raw.startswith("["):
            return json.loads(raw)
        return float(raw) if "." in raw else int(raw)

    # ── DB init ───────────────────────────────────────────────
    def _init_db(self):
        cfg.db_filename = f"{cfg.project_name}_{cfg.users}users_{cfg.runfor}mi_duration_{time.time()}.db"
        shutil.copy("./templates/template.db", f"./db/{cfg.db_filename}")
        #self.lbl_db.set(cfg.db_filename)
        self.root.title(f"⚡ Performance Bench Test — Control Panel - [{cfg.db_filename}]")

    # ── Start ─────────────────────────────────────────────────
    def _start_test(self):
        if not self._apply_params():
            return

        cfg.avg=0
        cfg.total_response_time=0
        cfg.samples_started=0
        cfg.samples_completed=0
        cfg.running_users=0
        cfg.current_errors=0
        cfg.error_percent=0
        cfg.el=0
        cfg.stop_requested = False
        self._init_db()
        self._stop_flag      = False         # ← reset global stop flag
        self._test_done_flag = False
        self._total_suites = max(1, (cfg.stop_at_user - cfg.users) // max(1, cfg.user_step) + 1)
        self._suite_num    = 0
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress_var.set(0)

        #try:
        #    with open("./data.json") as f:
        #        cfg.requests_data = json.load(f)
        #except Exception:
        #    pass

        self._log("━" * 55, "sep")
        self._log(f"TEST STARTED  ·  Project: {cfg.project_name}", "info")
        self._log(f"DB file: {cfg.db_filename}", "muted")
        self._log("━" * 55, "sep")

        threading.Thread(target=self._run_all_suites, daemon=True).start()
        self._tick()

    # ── Stop ──────────────────────────────────────────────────
    def _stop_test(self):
        self._stop_flag     = True
        cfg.stop_requested = True
        cfg.error_percent   = cfg.error_threshold
        self._log("⛔  Stop requested by user.", "warn")
        self.btn_stop.configure(state="disabled")
        self.progress_lbl.config(text="Stopping…")

    # ── Test loop (background thread) ─────────────────────────
    def _run_all_suites(self):
        
        runnable_tasks = [obj for name, obj in inspect.getmembers(api_requests) if
                      inspect.isfunction(obj) and getattr(obj, 'is_task', False)
                      and getattr(obj, 'enabled', True) ]
        
        w = [runnable_task.weight for runnable_task in runnable_tasks]        
                      
        while cfg.users > 0 and cfg.users <= cfg.stop_at_user:
            if self._stop_flag or cfg.stop_requested:
                break

            self._suite_num    += 1
            cfg.suite_id        = str(uuid.uuid4())
            cfg.test_start_time = time.time()
            cfg.current_errors  = 0
            cfg.samples_started = 0
            cfg.samples_completed = 0
            cfg.running_users   = 0
            cfg.error_percent   = 0
            task_list = task_propotion(runnable_tasks, cfg.users, w)

            pct = min(100, int((self._suite_num - 1) / self._total_suites * 100))
            self.root.after(0, lambda p=pct: self.progress_var.set(p))
            self.root.after(0, lambda: self.progress_lbl.config(
                text=f"Suite {self._suite_num}/{self._total_suites}  ·  {cfg.users} users  ·  {cfg.runfor} min"))

            self._log(f"▶  Suite {self._suite_num}  ·  Users: {cfg.users}  ·  Duration: {cfg.runfor} min", "info")

            threads = []
            for idx in range(cfg.users):
                if self._stop_flag or cfg.stop_requested:
                    break
                    
                api_requests_instance = api_requests()
                selected_thread_task = task_list[idx]
                thread_task = selected_thread_task.__get__(api_requests_instance, api_requests)
                
                cfg.running_users = idx + 1
                t_name  = f"User-{idx+1}"
                worker  = UserThread(t_name, thread_task, self._log)
                t = threading.Thread(target=worker.run, daemon=True)
                threads.append(t)
                t.start()
                self._log(f"   🟢 Started {t_name}", "muted")

                if idx < cfg.users - 1:
                    ramp  = cfg.rampup_per_user
                    delay = random.choice(ramp) if isinstance(ramp, list) else ramp
                    time.sleep(delay)

            cfg.test_start_time = time.time()

            # non-blocking join: poll every 0.5 s so stop flag is detected quickly
            while any(t.is_alive() for t in threads):
                if cfg.stop_requested:
                    break
                time.sleep(0.5)

            # wait for all threads to fully exit before continuing
            for t in threads:
                t.join(timeout=2)

            self._log(f"■  Suite {self._suite_num} done  ·  Samples: {cfg.samples_started}"
                      f"  ·  Errors: {cfg.current_errors}"
                      f"  ·  Error%: {cfg.error_percent:.2f}%", "warn")

            if cfg.error_percent >= cfg.error_threshold:
                self._log("⛔  Error threshold reached.", "err")
                break

            if cfg.stop_requested or self._stop_flag :
                self._log("⚠️  Stop requested, ending test.", "warn")
                break

            cfg.users += cfg.user_step

        self.root.after(0, lambda: self.progress_var.set(100))
        self.root.after(0, lambda: self.progress_lbl.config(text="✅  Test complete"))
        self._log("━" * 55, "sep")
        self._log(f"✅  ALL SUITES COMPLETE  ·  DB: ./db/{cfg.db_filename}", "ok")
        self._log("━" * 55, "sep")
        self.root.after(0, lambda: self.btn_start.configure(state="normal"))
        self.root.after(0, lambda: self.btn_stop.configure(state="disabled"))
        self._test_done_flag=True

    # ── Chart helpers ─────────────────────────────────────────
    def _init_chart_axes(self):
        for ax, title, colour in [
            (self._ax_rt,  "Avg Response Time (s)", "#1a7a4a"),
            (self._ax_tps, "Throughput (t/s)",       "#7c4daa"),
            (self._ax_tpm, "Transactions / min",      "#1e3a5f"),
            (self._ax_eff, "Efficiency (%)",          "#b85c00"),
        ]:
            ax.set_title(title, fontsize=7, color="#1a1a2e", pad=3)
            ax.tick_params(labelsize=6)
            ax.set_facecolor("#eef2f7")
            ax.grid(True, linestyle="--", linewidth=0.4, color="#cccccc")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.plot([], [], color=colour, linewidth=1.4)

    def _update_chart(self, elapsed, avg_rt, tps, tpm, eff):
        self._chart_time.append(elapsed)
        self._chart_avg_rt.append(avg_rt)
        self._chart_tps.append(tps)
        self._chart_tpm.append(tpm)
        self._chart_eff.append(eff)

        for lst in (self._chart_time, self._chart_avg_rt,
                    self._chart_tps, self._chart_tpm, self._chart_eff):
            if len(lst) > self._MAX_POINTS:
                del lst[0]

        t = self._chart_time

        def _redraw(ax, data, colour, label):
            ax.cla()
            ax.set_title(label, fontsize=7, color="#1a1a2e", pad=3)
            ax.tick_params(labelsize=6)
            ax.set_facecolor("#eef2f7")
            ax.grid(True, linestyle="--", linewidth=0.4, color="#cccccc")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.plot(t, data, color=colour, linewidth=1.4)
            if data:
                ax.set_xlim(t[0], max(t[-1], t[0] + 1))
                ax.fill_between(t, data, alpha=0.12, color=colour)
                ax.annotate(f"{data[-1]:.2f}", xy=(t[-1], data[-1]),
                            fontsize=6, color=colour,
                            xytext=(3, 3), textcoords="offset points")

        _redraw(self._ax_rt,  self._chart_avg_rt, "#1a7a4a", "Avg Response Time (s)")
        _redraw(self._ax_tps, self._chart_tps,    "#7c4daa", "Throughput (t/s)")
        _redraw(self._ax_tpm, self._chart_tpm,    "#1e3a5f", "Transactions / min")
        _redraw(self._ax_eff, self._chart_eff,    "#b85c00", "Efficiency (%)")

        self._canvas.draw_idle()

    # ── Live ticker (every 1 s) ───────────────────────────────
    def _tick(self):
        if not self._stop_flag and not self._test_done_flag:
            self.lbl_users.set(str(cfg.running_users))
            self.lbl_samples.set(str(cfg.samples_started))
            self.lbl_errors.set(str(cfg.current_errors))
            self.lbl_error_pct.set(f"{cfg.error_percent:.1f}%")
            if cfg.test_start_time:
                self.users = max(cfg.running_users, self.users)
                cfg.el += 1
                self.lbl_elapsed.set(f"{cfg.el//60:02d}:{cfg.el%60:02d}")
                try:
                    el = int(cfg.el) or 1
                    tps = cfg.samples_started / el
                    tpm = tps * 60
                    ttp = round(self.users / cfg.avg, 2) if cfg.avg else 0
                    eff = round((tps / (self.users / cfg.avg)) * 100, 1) if cfg.avg else 0
                    self.lbl_metrics.set(
                        f"{cfg.avg:.2f}s - {tps:.2f}t/s - {ttp:.2f}t/s - {eff:.0f}%"
                    )
                    self._update_chart(
                        elapsed=el,
                        avg_rt=round(cfg.avg, 3),
                        tps=round(tps, 3),
                        tpm=round(tpm, 2),
                        eff=round(eff, 1),
                    )
                except Exception:
                    pass
            self.root.after(1000, self._tick)
        else:
            pass


# ══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = BenchUI(root)
    root.mainloop()

