# -*- coding: utf-8 -*-
"""
Over the Hill (Demo) — Save Patcher  (современный интерфейс на CustomTkinter)
Выбираешь папку сохранений, отмечаешь патчи, жмёшь «Применить». Авто-бэкап + откат.
"""
import os, sys, json, shutil, glob, datetime, webbrowser
import ctypes
from ctypes import wintypes
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw

# --- WinAPI: показать безрамочное окно в панели задач ---
GWL_EXSTYLE = -20; WS_EX_APPWINDOW = 0x00040000; WS_EX_TOOLWINDOW = 0x00000080; SW_MINIMIZE = 6
_u32 = ctypes.windll.user32
_u32.GetParent.restype = wintypes.HWND; _u32.GetParent.argtypes = [wintypes.HWND]
try:
    _GetLong, _SetLong = _u32.GetWindowLongPtrW, _u32.SetWindowLongPtrW
except AttributeError:
    _GetLong, _SetLong = _u32.GetWindowLongW, _u32.SetWindowLongW
_GetLong.restype = ctypes.c_ssize_t; _GetLong.argtypes = [wintypes.HWND, ctypes.c_int]
_SetLong.restype = ctypes.c_ssize_t; _SetLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]

APP_TITLE = "Over the Hill — Патчер"
PROC_NAMES = ("over the hill.exe", "over the hill")
ACCENT = "#E8A33D"; ACCENT_HOVER = "#cf8e2c"
SUPPORT_URL = "https://t.me/watuqator1"
TG_BLUE = "#229ED9"

def make_tg_icon(px=22):
    """Иконка Telegram (синий кружок + белый самолётик), рисуется на лету."""
    s = px * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s - 1, s - 1], fill=TG_BLUE)
    sc = lambda pts: [(x / 256 * s, y / 256 * s) for x, y in pts]
    plane = [(46, 120), (200, 60), (168, 176), (120, 148), (96, 178), (96, 142)]
    d.polygon(sc(plane), fill="white")
    d.polygon(sc([(120, 148), (96, 178), (96, 142)]), fill="#cfe7f6")  # тень сгиба
    return img.resize((px, px), Image.LANCZOS)

# ---------- данные ----------
def resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

with open(resource_path("data.json"), encoding="utf-8") as f:
    DATA = json.load(f)

MONEY_ID      = int(DATA["money_id"])
DRIVABLE_CARS = [int(k) for k in DATA["drivable_cars"].keys()]
COSMETICS     = [int(k) for k in DATA["cosmetics"].keys()]
LIVERIES      = [int(k) for k in DATA["liveries"].keys()]
TOOLS         = [int(k) for k in DATA["tools"].keys()]
CABINS        = [int(k) for k in DATA["cabins"].keys()]
POI_GENERIC   = [int(x) for x in DATA["poi_generic"]]
SCENIC        = [int(x) for x in DATA["scenic"]]
CAR_TEMPLATE  = [int(x) for x in DATA["car_template_18"]]

# ---------- утилиты ----------
def game_running():
    try:
        import psutil
        for p in psutil.process_iter(["name"]):
            if (p.info.get("name") or "").lower() in PROC_NAMES:
                return True
    except Exception:
        pass
    return False

def default_saves_root():
    d = os.path.join(os.path.expanduser("~"), "Documents", "My Games", "over the hill")
    return d if os.path.isdir(d) else ""

def find_profiles(root):
    sd = os.path.join(root, "Saves")
    if not os.path.isdir(sd):
        return []
    return sorted(os.path.basename(p) for p in glob.glob(os.path.join(sd, "*.json"))
                  if not p.endswith(".bak"))

# ---------- операции над сейвом ----------
def _items(s):   return s["Profile"]["Inventory"]["Items"]
def _virtual(s): return s["Profile"]["Inventory"]["VirtualItems"]
def _stype(it):  return it["Type"].split(",")[0]

def patch_money(s, log):
    inv = {it["Data"]["ItemId"]: it for it in _items(s) if _stype(it) == "InventoryItem"}
    if MONEY_ID in inv: inv[MONEY_ID]["Data"]["Count"] = 9999999
    else: _items(s).append({"Type": "InventoryItem, Assembly-CSharp", "Data": {"ItemId": MONEY_ID, "Count": 9999999}})
    log("Деньги → 9 999 999")

def patch_inventory_items(s, ids, count, label, log):
    inv = {it["Data"]["ItemId"]: it for it in _items(s) if _stype(it) == "InventoryItem"}
    n = 0
    for iid in ids:
        if iid in inv:
            if inv[iid]["Data"].get("Count", 0) < count: inv[iid]["Data"]["Count"] = count
        else:
            _items(s).append({"Type": "InventoryItem, Assembly-CSharp", "Data": {"ItemId": iid, "Count": count}}); n += 1
    log(f"{label}: +{n} (всего {len(ids)})")

def patch_cosmetics(s, log):
    have = {it["Data"]["ItemId"] for it in _items(s) if _stype(it) == "VehicleSpecificItem"}
    n = 0
    for iid in COSMETICS:
        if iid not in have:
            states = [{"VehicleItemId": c, "Count": 1} for c in CAR_TEMPLATE]
            _items(s).append({"Type": "VehicleSpecificItem, Assembly-CSharp", "Data": {"ItemId": iid, "VehicleStates": states}}); n += 1
    log(f"Косметика: +{n} (всего {len(COSMETICS)})")

def patch_cars(s, log):
    have = {it["Data"]["ItemId"] for it in _items(s) if _stype(it) == "VehicleItem"}
    n = 0
    for iid in DRIVABLE_CARS:
        if iid not in have:
            _items(s).append({"Type": "VehicleItem, Assembly-CSharp",
                              "Data": {"ItemId": iid, "Count": 1, "InUse": False, "MetersTravelled": 0, "ToolsetIDs": []}}); n += 1
    log(f"Машины: +{n} (всего {len(DRIVABLE_CARS)})")

def patch_pois(s, ids, label, log):
    vlist = _virtual(s); have = {vi["Data"].get("ItemId") for vi in vlist}
    for vi in vlist:
        if vi["Data"].get("ItemId") in ids:
            vi["Data"]["State"] = 2; vi["Data"]["Completed"] = True
    n = 0
    for iid in ids:
        if iid not in have:
            vlist.append({"Type": "PointOfInterestData, Assembly-CSharp", "Data": {"ItemId": iid, "State": 2, "Completed": True}}); n += 1
    log(f"{label}: открыто {len(ids)}")

def patch_fog(root, log):
    files = glob.glob(os.path.join(root, "Saves", "FogOfWar", "*.fow"))
    if not files: log("Туман: .fow не найдены"); return
    for fp in files:
        shutil.copy(fp, fp + ".bak")
        with open(fp, "wb") as f: f.write(b"\xff" * os.path.getsize(fp))
    log(f"Туман снят: {len(files)} зон(а)")

# ---------- GUI ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

PATCHES = [
    ("money",     "💰  Деньги → 9 999 999"),
    ("cosmetics", "🎒  Вся косметика / аксессуары (134)"),
    ("liveries",  "🎨  Все покраски / ливреи (199)"),
    ("tools",     "🔧  Все инструменты (×99)"),
    ("cars",      "🚙  Ездовые машины demo (3)"),
    ("cabins",    "🏠  Открыть все хижины (6)"),
    ("poi",       "📦  Открыть все точки интереса (18)"),
    ("scenic",    "⛰  Открыть смотровые точки (2)"),
    ("fog",       "🗺  Снять весь туман войны"),
]

WIN_W, WIN_H = 560, 880
BORDER = "#2a2a2a"; BAR = "#1b1b1b"; BG = "#242424"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QB Over The Hill (DEMO)")
        self.overrideredirect(True)                 # убрать системную рамку
        self.configure(fg_color=BORDER)
        x = (self.winfo_screenwidth() - WIN_W) // 2
        y = (self.winfo_screenheight() - WIN_H) // 2
        self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")
        self._appwin = False
        self.after(12, self._set_appwindow)   # вернуть кнопку в панель задач

        # внешняя рамка (тонкая граница)
        outer = ctk.CTkFrame(self, corner_radius=0, fg_color=BG,
                             border_width=1, border_color="#3a3a3a")
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        # ----- кастомный титл-бар -----
        bar = ctk.CTkFrame(outer, height=40, corner_radius=0, fg_color=BAR)
        bar.pack(fill="x"); bar.pack_propagate(False)
        title = ctk.CTkLabel(bar, text="  QB  ", font=ctk.CTkFont(size=15, weight="bold"),
                             fg_color=ACCENT, text_color="#1a1a1a", corner_radius=6)
        title.pack(side="left", padx=(10, 8), pady=8)
        ctk.CTkLabel(bar, text="Over The Hill  (DEMO)", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e6e6e6").pack(side="left")
        # кнопки окна
        ctk.CTkButton(bar, text="✕", width=40, height=40, corner_radius=0, fg_color=BAR,
                      hover_color="#c0392b", text_color="#cfcfcf",
                      font=ctk.CTkFont(size=15), command=self.destroy).pack(side="right")
        ctk.CTkButton(bar, text="—", width=40, height=40, corner_radius=0, fg_color=BAR,
                      hover_color="#3a3a3a", text_color="#cfcfcf",
                      font=ctk.CTkFont(size=15), command=self._minimize).pack(side="right")
        for w in (bar, title):
            w.bind("<Button-1>", self._start_move)
            w.bind("<B1-Motion>", self._on_move)

        # header
        head = ctk.CTkFrame(outer, fg_color="transparent"); head.pack(fill="x", padx=20, pady=(16, 6))
        ctk.CTkLabel(head, text="OVER THE HILL", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT).pack(anchor="w")
        ctk.CTkLabel(head, text="Патчер сохранения · демо", font=ctk.CTkFont(size=13),
                     text_color="#9aa0a6").pack(anchor="w")

        self.root = outer    # дальше всё кладём в outer

        # путь + профиль (карточка)
        card = ctk.CTkFrame(self.root, corner_radius=12); card.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(card, text="Папка сохранений", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=14, pady=(12, 2))
        prow = ctk.CTkFrame(card, fg_color="transparent"); prow.pack(fill="x", padx=14)
        self.var_root = ctk.StringVar()
        ctk.CTkEntry(prow, textvariable=self.var_root).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(prow, text="Обзор", width=70, command=self._browse).pack(side="left", padx=(8, 0))
        # подсказка с типичным путём
        ctk.CTkLabel(card, text="Обычно: C:\\Users\\<имя>\\Documents\\My Games\\over the hill",
                     font=ctk.CTkFont(size=11), text_color="#7d8288").pack(anchor="w", padx=14, pady=(4, 0))
        ctk.CTkLabel(card, text="Папка определяется сама. Если нет — нажми «Обзор» и укажи её вручную.",
                     font=ctk.CTkFont(size=11), text_color="#7d8288").pack(anchor="w", padx=14, pady=(1, 0))
        prow2 = ctk.CTkFrame(card, fg_color="transparent"); prow2.pack(fill="x", padx=14, pady=(8, 14))
        ctk.CTkLabel(prow2, text="Профиль").pack(side="left")
        self.var_profile = ctk.StringVar(value="—")
        self.opt = ctk.CTkOptionMenu(prow2, variable=self.var_profile, values=["—"], width=180)
        self.opt.pack(side="left", padx=8)
        self.dot = ctk.CTkLabel(prow2, text="●  игра закрыта", text_color="#5cb85c", font=ctk.CTkFont(size=12))
        self.dot.pack(side="right")

        # патчи (натуральная высота, без растягивания)
        ctk.CTkLabel(self.root, text="Патчи", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=24, pady=(8, 0))
        body = ctk.CTkFrame(self.root, corner_radius=12); body.pack(fill="x", padx=20, pady=6)
        toprow = ctk.CTkFrame(body, fg_color="transparent"); toprow.pack(fill="x", padx=14, pady=(10, 2))
        self.var_all = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(toprow, text="Выбрать всё", variable=self.var_all, command=self._toggle_all,
                      progress_color=ACCENT).pack(anchor="w")
        ctk.CTkFrame(body, height=1, fg_color="#3a3a3a").pack(fill="x", padx=14, pady=4)
        self.checks = {}
        for key, label in PATCHES:
            v = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(body, text=label, variable=v, font=ctk.CTkFont(size=13),
                            fg_color=ACCENT, hover_color=ACCENT_HOVER).pack(anchor="w", padx=18, pady=3)
            self.checks[key] = v
        ctk.CTkFrame(body, height=6, fg_color="transparent").pack()

        # кнопки
        brow = ctk.CTkFrame(self.root, fg_color="transparent"); brow.pack(fill="x", padx=20, pady=(6, 4))
        ctk.CTkButton(brow, text="Применить", height=42, font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#1a1a1a",
                      command=self._apply).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(brow, text="Откат", width=90, height=42, fg_color="#3a3a3a", hover_color="#4a4a4a",
                      command=self._restore).pack(side="left", padx=(8, 0))

        # лог
        self.log_box = ctk.CTkTextbox(self.root, height=88, corner_radius=10, font=ctk.CTkFont(size=12))
        self.log_box.pack(fill="x", padx=20, pady=(2, 4))

        # футер — поддержка в Telegram
        footer = ctk.CTkFrame(self.root, fg_color="transparent"); footer.pack(fill="x", pady=(2, 10))
        self.tg_img = ctk.CTkImage(make_tg_icon(20), size=(20, 20))
        ctk.CTkButton(footer, text="  Поддержка · Telegram", image=self.tg_img, compound="left",
                      fg_color="transparent", hover_color="#2a2a2a", text_color=TG_BLUE,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=lambda: webbrowser.open(SUPPORT_URL)).pack()

        self._autodetect()
        self._poll_game()
        self.after(30, self._fit_height)   # подогнать высоту окна под контент

    def _fit_height(self):
        self.update_idletasks()
        h = self.root.winfo_reqheight() + 4
        x = (self.winfo_screenwidth() - WIN_W) // 2
        y = max(0, (self.winfo_screenheight() - h) // 3)
        self.geometry(f"{WIN_W}x{h}+{x}+{y}")

    # ---- кастомная рамка: перетаскивание и сворачивание ----
    def _start_move(self, e): self._ox, self._oy = e.x_root - self.winfo_x(), e.y_root - self.winfo_y()
    def _on_move(self, e):    self.geometry(f"+{e.x_root - self._ox}+{e.y_root - self._oy}")
    def _hwnd(self):
        return _u32.GetParent(self.winfo_id())
    def _set_appwindow(self):
        if self._appwin: return
        hwnd = self._hwnd()
        st = _GetLong(hwnd, GWL_EXSTYLE)
        st = (st & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW
        _SetLong(hwnd, GWL_EXSTYLE, st)
        self._appwin = True
        self.wm_withdraw(); self.after(10, self.wm_deiconify)   # применить стиль
    def _minimize(self):
        _u32.ShowWindow(self._hwnd(), SW_MINIMIZE)

    # helpers
    def log(self, m): self.log_box.insert("end", m + "\n"); self.log_box.see("end")
    def _toggle_all(self):
        for v in self.checks.values(): v.set(self.var_all.get())

    def _poll_game(self):
        if game_running():
            self.dot.configure(text="●  игра запущена — закрой", text_color="#e05c5c")
        else:
            self.dot.configure(text="●  игра закрыта", text_color="#5cb85c")
        self.after(2000, self._poll_game)

    def _autodetect(self):
        root = default_saves_root()
        if root: self.var_root.set(root); self._refresh(); self.log("Папка сохранений найдена автоматически.")
        else: self.log("Папка не найдена — укажи через «Обзор».")

    def _browse(self):
        d = filedialog.askdirectory(title="Папка сохранений или директория игры")
        if not d: return
        self.var_root.set(d if os.path.isdir(os.path.join(d, "Saves")) else (default_saves_root() or d))
        self._refresh()

    def _refresh(self):
        profs = find_profiles(self.var_root.get())
        self.opt.configure(values=profs or ["—"])
        self.var_profile.set(profs[0] if profs else "—")
        self.log(f"Профили: {', '.join(profs) if profs else 'нет'}")

    def _save_path(self):
        return os.path.join(self.var_root.get(), "Saves", self.var_profile.get())

    def _apply(self):
        if game_running():
            messagebox.showwarning(APP_TITLE, "Игра запущена! Закрой её полностью."); return
        sp = self._save_path()
        if not os.path.isfile(sp):
            messagebox.showerror(APP_TITLE, f"Файл не найден:\n{sp}"); return
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = sp + f".patcher_{stamp}.bak"; shutil.copy(sp, bak)
        self.log(f"Бэкап: {os.path.basename(bak)}")
        try:
            s = json.load(open(sp, encoding="utf-8")); c = self.checks
            if c["money"].get():     patch_money(s, self.log)
            if c["cosmetics"].get(): patch_cosmetics(s, self.log)
            if c["liveries"].get():  patch_inventory_items(s, LIVERIES, 1, "Ливреи", self.log)
            if c["tools"].get():     patch_inventory_items(s, TOOLS, 99, "Инструменты", self.log)
            if c["cars"].get():      patch_cars(s, self.log)
            if c["cabins"].get():    patch_pois(s, CABINS, "Хижины", self.log)
            if c["poi"].get():       patch_pois(s, POI_GENERIC, "Точки интереса", self.log)
            if c["scenic"].get():    patch_pois(s, SCENIC, "Смотровые", self.log)
            json.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            shutil.copy(sp, sp + ".bak")
            if c["fog"].get():       patch_fog(self.var_root.get(), self.log)
            self.log("✓ ГОТОВО. Запускай игру.")
            messagebox.showinfo(APP_TITLE, "Патчи применены. Запускай игру.")
        except Exception as e:
            shutil.copy(bak, sp)
            self.log(f"✗ ОШИБКА: {e} — сейв откатан."); messagebox.showerror(APP_TITLE, str(e))

    def _restore(self):
        if game_running():
            messagebox.showwarning(APP_TITLE, "Закрой игру перед откатом."); return
        sp = self._save_path()
        baks = sorted(glob.glob(sp + ".patcher_*.bak"), key=os.path.getmtime)
        if not baks: messagebox.showinfo(APP_TITLE, "Бэкапов патчера нет."); return
        shutil.copy(baks[-1], sp); shutil.copy(baks[-1], sp + ".bak")
        self.log(f"Откат: {os.path.basename(baks[-1])}")
        messagebox.showinfo(APP_TITLE, "Сейв восстановлен.")

if __name__ == "__main__":
    App().mainloop()
