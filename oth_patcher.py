# -*- coding: utf-8 -*-
"""
Over the Hill (Demo) — Save Patcher  (RU/EN, CustomTkinter, кастомная рамка)
Выбираешь папку сохранений, отмечаешь патчи, жмёшь «Применить». Авто-бэкап + откат.
"""
import os, sys, json, shutil, glob, datetime, webbrowser
import ctypes
from ctypes import wintypes
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw

PROC_NAMES = ("over the hill.exe", "over the hill")
ACCENT = "#E8A33D"; ACCENT_HOVER = "#cf8e2c"
SUPPORT_URL = "https://t.me/watuqator1"
TG_BLUE = "#229ED9"

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

# ---------- локализация ----------
LANG = {
 "ru": {
  "subtitle": "Патчер сохранения · демо",
  "saves_folder": "Папка сохранений", "browse": "Обзор", "profile": "Профиль",
  "hint_path": "Обычно: C:\\Users\\<имя>\\Documents\\My Games\\over the hill",
  "hint_auto": "Папка определяется сама. Если нет — нажми «Обзор» и укажи её вручную.",
  "game_closed": "● игра закрыта", "game_running": "● игра запущена — закрой",
  "patches": "Патчи", "select_all": "Выбрать всё", "apply": "Применить", "restore": "Откат",
  "support": "  Поддержка · Telegram",
  "log_profiles": "Профили: {}", "none": "нет",
  "log_autofound": "Папка сохранений найдена автоматически.",
  "log_notfound": "Папка не найдена — укажи через «Обзор».",
  "log_backup": "Бэкап: {}", "log_done": "✓ ГОТОВО. Запускай игру.",
  "msg_running": "Игра запущена! Закрой её полностью.",
  "msg_notfound": "Файл не найден:\n{}", "msg_applied": "Патчи применены. Запускай игру.",
  "msg_no_backups": "Бэкапов патчера нет.", "msg_restored": "Сейв восстановлен.",
  "msg_close_restore": "Закрой игру перед откатом.",
  "p_money": "Деньги → 9 999 999", "p_cosmetics": "Вся косметика / аксессуары (134)",
  "p_liveries": "Все покраски / ливреи (199)", "p_tools": "Все инструменты (×99)",
  "p_cars": "Ездовые машины demo (3)", "p_cabins": "Открыть все хижины (6)",
  "p_poi": "Открыть все точки интереса (18)", "p_scenic": "Открыть смотровые точки (2)",
  "p_fog": "Снять весь туман войны",
  "added": "добавлено", "total": "всего", "opened": "открыто",
 },
 "en": {
  "subtitle": "Save patcher · demo",
  "saves_folder": "Save folder", "browse": "Browse", "profile": "Profile",
  "hint_path": "Usually: C:\\Users\\<name>\\Documents\\My Games\\over the hill",
  "hint_auto": "The folder is auto-detected. If not — click \"Browse\" and select it.",
  "game_closed": "● game closed", "game_running": "● game running — close it",
  "patches": "Patches", "select_all": "Select all", "apply": "Apply", "restore": "Restore",
  "support": "  Support · Telegram",
  "log_profiles": "Profiles: {}", "none": "none",
  "log_autofound": "Save folder detected automatically.",
  "log_notfound": "Folder not found — set it via \"Browse\".",
  "log_backup": "Backup: {}", "log_done": "✓ DONE. Launch the game.",
  "msg_running": "The game is running! Close it completely.",
  "msg_notfound": "File not found:\n{}", "msg_applied": "Patches applied. Launch the game.",
  "msg_no_backups": "No patcher backups found.", "msg_restored": "Save restored.",
  "msg_close_restore": "Close the game before restoring.",
  "p_money": "Money → 9,999,999", "p_cosmetics": "All cosmetics / accessories (134)",
  "p_liveries": "All paints / liveries (199)", "p_tools": "All tools (×99)",
  "p_cars": "Drivable demo cars (3)", "p_cabins": "Unlock all cabins (6)",
  "p_poi": "Unlock all points of interest (18)", "p_scenic": "Unlock scenic lookouts (2)",
  "p_fog": "Clear all fog of war",
  "added": "added", "total": "total", "opened": "opened",
 },
}
def default_lang():
    try:  # язык интерфейса Windows; русский = LANGID 0x19
        if (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF) == 0x19:
            return "ru"
    except Exception:
        pass
    return "en"

# patch key, emoji, translation-key
PATCHES = [
    ("money",     "💰", "p_money"),
    ("cosmetics", "🎒", "p_cosmetics"),
    ("liveries",  "🎨", "p_liveries"),
    ("tools",     "🔧", "p_tools"),
    ("cars",      "🚙", "p_cars"),
    ("cabins",    "🏠", "p_cabins"),
    ("poi",       "📦", "p_poi"),
    ("scenic",    "⛰", "p_scenic"),
    ("fog",       "🗺", "p_fog"),
]

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

def patch_money(s, label, t, log):
    inv = {it["Data"]["ItemId"]: it for it in _items(s) if _stype(it) == "InventoryItem"}
    if MONEY_ID in inv: inv[MONEY_ID]["Data"]["Count"] = 9999999
    else: _items(s).append({"Type": "InventoryItem, Assembly-CSharp", "Data": {"ItemId": MONEY_ID, "Count": 9999999}})
    log(label)

def patch_inventory_items(s, ids, count, label, t, log):
    inv = {it["Data"]["ItemId"]: it for it in _items(s) if _stype(it) == "InventoryItem"}
    n = 0
    for iid in ids:
        if iid in inv:
            if inv[iid]["Data"].get("Count", 0) < count: inv[iid]["Data"]["Count"] = count
        else:
            _items(s).append({"Type": "InventoryItem, Assembly-CSharp", "Data": {"ItemId": iid, "Count": count}}); n += 1
    log(f"{label}: +{n}")

def patch_cosmetics(s, label, t, log):
    have = {it["Data"]["ItemId"] for it in _items(s) if _stype(it) == "VehicleSpecificItem"}
    n = 0
    for iid in COSMETICS:
        if iid not in have:
            states = [{"VehicleItemId": c, "Count": 1} for c in CAR_TEMPLATE]
            _items(s).append({"Type": "VehicleSpecificItem, Assembly-CSharp", "Data": {"ItemId": iid, "VehicleStates": states}}); n += 1
    log(f"{label}: +{n}")

def patch_cars(s, label, t, log):
    have = {it["Data"]["ItemId"] for it in _items(s) if _stype(it) == "VehicleItem"}
    n = 0
    for iid in DRIVABLE_CARS:
        if iid not in have:
            _items(s).append({"Type": "VehicleItem, Assembly-CSharp",
                              "Data": {"ItemId": iid, "Count": 1, "InUse": False, "MetersTravelled": 0, "ToolsetIDs": []}}); n += 1
    log(f"{label}: +{n}")

def patch_pois(s, ids, label, t, log):
    vlist = _virtual(s); have = {vi["Data"].get("ItemId") for vi in vlist}
    for vi in vlist:
        if vi["Data"].get("ItemId") in ids:
            vi["Data"]["State"] = 2; vi["Data"]["Completed"] = True
    for iid in ids:
        if iid not in have:
            vlist.append({"Type": "PointOfInterestData, Assembly-CSharp", "Data": {"ItemId": iid, "State": 2, "Completed": True}})
    log(f"{label}: {t('opened')} {len(ids)}")

def patch_fog(root, t, log):
    files = glob.glob(os.path.join(root, "Saves", "FogOfWar", "*.fow"))
    if not files: log("fog: .fow not found"); return
    for fp in files:
        shutil.copy(fp, fp + ".bak")
        with open(fp, "wb") as f: f.write(b"\xff" * os.path.getsize(fp))
    log(f"fog: {len(files)}")

# ---------- иконка Telegram ----------
def make_tg_icon(px=20):
    s = px * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.ellipse([0, 0, s - 1, s - 1], fill=TG_BLUE)
    sc = lambda pts: [(x / 256 * s, y / 256 * s) for x, y in pts]
    d.polygon(sc([(46,120),(200,60),(168,176),(120,148),(96,178),(96,142)]), fill="white")
    d.polygon(sc([(120,148),(96,178),(96,142)]), fill="#cfe7f6")
    return img.resize((px, px), Image.LANCZOS)

# ---------- GUI ----------
ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("dark-blue")
WIN_W, WIN_H = 560, 900
BAR = "#1b1b1b"; BG = "#242424"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.lang = default_lang()
        self.title("QB Over The Hill (DEMO)")
        self.overrideredirect(True); self.configure(fg_color="#2a2a2a")
        x = (self.winfo_screenwidth() - WIN_W) // 2; y = (self.winfo_screenheight() - WIN_H) // 2
        self.geometry(f"{WIN_W}x{WIN_H}+{x}+{y}")
        self._appwin = False; self.after(12, self._set_appwindow)

        outer = ctk.CTkFrame(self, corner_radius=0, fg_color=BG, border_width=1, border_color="#3a3a3a")
        outer.pack(fill="both", expand=True, padx=2, pady=2); self.root = outer

        # ----- титл-бар -----
        bar = ctk.CTkFrame(outer, height=40, corner_radius=0, fg_color=BAR); bar.pack(fill="x"); bar.pack_propagate(False)
        title = ctk.CTkLabel(bar, text="  QB  ", font=ctk.CTkFont(size=15, weight="bold"),
                             fg_color=ACCENT, text_color="#1a1a1a", corner_radius=6)
        title.pack(side="left", padx=(10, 8), pady=8)
        ctk.CTkLabel(bar, text="Over The Hill  (DEMO)", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e6e6e6").pack(side="left")
        ctk.CTkButton(bar, text="✕", width=40, height=40, corner_radius=0, fg_color=BAR,
                      hover_color="#c0392b", text_color="#cfcfcf", font=ctk.CTkFont(size=15),
                      command=self.destroy).pack(side="right")
        ctk.CTkButton(bar, text="—", width=40, height=40, corner_radius=0, fg_color=BAR,
                      hover_color="#3a3a3a", text_color="#cfcfcf", font=ctk.CTkFont(size=15),
                      command=self._minimize).pack(side="right")
        # переключатель языка
        self.seg = ctk.CTkSegmentedButton(bar, values=["RU", "EN"], width=92, height=26,
                     command=self._on_lang, selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
                     font=ctk.CTkFont(size=12, weight="bold"))
        self.seg.set("RU" if self.lang == "ru" else "EN")
        self.seg.pack(side="right", padx=10)
        for w in (bar, title):
            w.bind("<Button-1>", self._start_move); w.bind("<B1-Motion>", self._on_move)

        # ----- header -----
        head = ctk.CTkFrame(outer, fg_color="transparent"); head.pack(fill="x", padx=20, pady=(16, 6))
        ctk.CTkLabel(head, text="OVER THE HILL", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT).pack(anchor="w")
        self.lbl_subtitle = ctk.CTkLabel(head, text="", font=ctk.CTkFont(size=13), text_color="#9aa0a6")
        self.lbl_subtitle.pack(anchor="w")

        # ----- карточка пути -----
        card = ctk.CTkFrame(outer, corner_radius=12); card.pack(fill="x", padx=20, pady=8)
        self.lbl_saves = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_saves.pack(anchor="w", padx=14, pady=(12, 2))
        prow = ctk.CTkFrame(card, fg_color="transparent"); prow.pack(fill="x", padx=14)
        self.var_root = ctk.StringVar()
        ctk.CTkEntry(prow, textvariable=self.var_root).pack(side="left", fill="x", expand=True)
        self.btn_browse = ctk.CTkButton(prow, text="", width=70, command=self._browse); self.btn_browse.pack(side="left", padx=(8, 0))
        self.lbl_hint1 = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color="#7d8288")
        self.lbl_hint1.pack(anchor="w", padx=14, pady=(4, 0))
        self.lbl_hint2 = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=11), text_color="#7d8288")
        self.lbl_hint2.pack(anchor="w", padx=14, pady=(1, 0))
        prow2 = ctk.CTkFrame(card, fg_color="transparent"); prow2.pack(fill="x", padx=14, pady=(8, 14))
        self.lbl_profile = ctk.CTkLabel(prow2, text=""); self.lbl_profile.pack(side="left")
        self.var_profile = ctk.StringVar(value="—")
        self.opt = ctk.CTkOptionMenu(prow2, variable=self.var_profile, values=["—"], width=170); self.opt.pack(side="left", padx=8)
        self.dot = ctk.CTkLabel(prow2, text="", text_color="#5cb85c", font=ctk.CTkFont(size=12)); self.dot.pack(side="right")

        # ----- патчи -----
        self.lbl_patches = ctk.CTkLabel(outer, text="", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_patches.pack(anchor="w", padx=24, pady=(8, 0))
        body = ctk.CTkFrame(outer, corner_radius=12); body.pack(fill="x", padx=20, pady=6)
        self.var_all = ctk.BooleanVar(value=True)
        self.sw_all = ctk.CTkSwitch(body, text="", variable=self.var_all, command=self._toggle_all, progress_color=ACCENT)
        self.sw_all.pack(anchor="w", padx=18, pady=(12, 2))
        ctk.CTkFrame(body, height=1, fg_color="#3a3a3a").pack(fill="x", padx=14, pady=4)
        self.checks = {}; self.check_widgets = []
        for key, emoji, tkey in PATCHES:
            v = ctk.BooleanVar(value=True)
            cb = ctk.CTkCheckBox(body, text="", variable=v, font=ctk.CTkFont(size=13), fg_color=ACCENT, hover_color=ACCENT_HOVER)
            cb.pack(anchor="w", padx=18, pady=3)
            self.checks[key] = v; self.check_widgets.append((cb, emoji, tkey))
        ctk.CTkFrame(body, height=6, fg_color="transparent").pack()

        # ----- футер: поддержка -----
        footer = ctk.CTkFrame(outer, fg_color="transparent")
        self.tg_img = ctk.CTkImage(make_tg_icon(20), size=(20, 20))
        self.btn_support = ctk.CTkButton(footer, text="", image=self.tg_img, compound="left",
                      fg_color="transparent", hover_color="#2a2a2a", text_color=TG_BLUE,
                      font=ctk.CTkFont(size=13, weight="bold"), command=lambda: webbrowser.open(SUPPORT_URL))
        self.btn_support.pack()
        footer.pack(side="bottom", fill="x", pady=(2, 10))
        self.log_box = ctk.CTkTextbox(outer, height=88, corner_radius=10, font=ctk.CTkFont(size=12))
        self.log_box.pack(side="bottom", fill="x", padx=20, pady=(2, 4))
        brow = ctk.CTkFrame(outer, fg_color="transparent"); brow.pack(side="bottom", fill="x", padx=20, pady=(6, 4))
        self.btn_apply = ctk.CTkButton(brow, text="", height=42, font=ctk.CTkFont(size=15, weight="bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#1a1a1a", command=self._apply)
        self.btn_apply.pack(side="left", fill="x", expand=True)
        self.btn_restore = ctk.CTkButton(brow, text="", width=90, height=42, fg_color="#3a3a3a",
                      hover_color="#4a4a4a", command=self._restore); self.btn_restore.pack(side="left", padx=(8, 0))

        self._retext()
        self._autodetect()
        self._poll_game()

    # ---- i18n ----
    def t(self, k): return LANG[self.lang].get(k, k)
    def _on_lang(self, val):
        self.lang = "ru" if val == "RU" else "en"
        self._retext(); self._update_dot()
        self.log_box.delete("1.0", "end")          # перелогировать статус на новом языке
        self._autodetect()
    def _retext(self):
        T = self.t
        self.lbl_subtitle.configure(text=T("subtitle"))
        self.lbl_saves.configure(text=T("saves_folder")); self.btn_browse.configure(text=T("browse"))
        self.lbl_hint1.configure(text=T("hint_path")); self.lbl_hint2.configure(text=T("hint_auto"))
        self.lbl_profile.configure(text=T("profile"))
        self.lbl_patches.configure(text=T("patches")); self.sw_all.configure(text=T("select_all"))
        self.btn_apply.configure(text=T("apply")); self.btn_restore.configure(text=T("restore"))
        self.btn_support.configure(text=T("support"))
        for cb, emoji, tkey in self.check_widgets:
            cb.configure(text=f"{emoji}  {T(tkey)}")

    # ---- кастомная рамка ----
    def _hwnd(self): return _u32.GetParent(self.winfo_id())
    def _set_appwindow(self):
        if self._appwin: return
        hwnd = self._hwnd(); st = _GetLong(hwnd, GWL_EXSTYLE)
        _SetLong(hwnd, GWL_EXSTYLE, (st & ~WS_EX_TOOLWINDOW) | WS_EX_APPWINDOW)
        self._appwin = True; self.wm_withdraw(); self.after(10, self.wm_deiconify)
    def _minimize(self): _u32.ShowWindow(self._hwnd(), SW_MINIMIZE)
    def _start_move(self, e): self._ox, self._oy = e.x_root - self.winfo_x(), e.y_root - self.winfo_y()
    def _on_move(self, e):    self.geometry(f"+{e.x_root - self._ox}+{e.y_root - self._oy}")

    # ---- helpers ----
    def log(self, m): self.log_box.insert("end", m + "\n"); self.log_box.see("end")
    def _toggle_all(self):
        for v in self.checks.values(): v.set(self.var_all.get())
    def _update_dot(self):
        if game_running(): self.dot.configure(text=self.t("game_running"), text_color="#e05c5c")
        else: self.dot.configure(text=self.t("game_closed"), text_color="#5cb85c")
    def _poll_game(self):
        self._update_dot(); self.after(2000, self._poll_game)
    def _autodetect(self):
        root = default_saves_root()
        if root: self.var_root.set(root); self._refresh(); self.log(self.t("log_autofound"))
        else: self.log(self.t("log_notfound"))
    def _browse(self):
        d = filedialog.askdirectory(title=self.t("saves_folder"))
        if not d: return
        self.var_root.set(d if os.path.isdir(os.path.join(d, "Saves")) else (default_saves_root() or d))
        self._refresh()
    def _refresh(self):
        profs = find_profiles(self.var_root.get())
        self.opt.configure(values=profs or ["—"]); self.var_profile.set(profs[0] if profs else "—")
        self.log(self.t("log_profiles").format(", ".join(profs) if profs else self.t("none")))
    def _save_path(self):
        return os.path.join(self.var_root.get(), "Saves", self.var_profile.get())

    def _apply(self):
        T = self.t
        if game_running(): messagebox.showwarning("", T("msg_running")); return
        sp = self._save_path()
        if not os.path.isfile(sp): messagebox.showerror("", T("msg_notfound").format(sp)); return
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = sp + f".patcher_{stamp}.bak"; shutil.copy(sp, bak)
        self.log(T("log_backup").format(os.path.basename(bak)))
        try:
            s = json.load(open(sp, encoding="utf-8")); c = self.checks
            L = {k: f"{e}  {T(tk)}".strip() for k, e, tk in PATCHES}
            if c["money"].get():     patch_money(s, T("p_money"), T, self.log)
            if c["cosmetics"].get(): patch_cosmetics(s, T("p_cosmetics"), T, self.log)
            if c["liveries"].get():  patch_inventory_items(s, LIVERIES, 1, T("p_liveries"), T, self.log)
            if c["tools"].get():     patch_inventory_items(s, TOOLS, 99, T("p_tools"), T, self.log)
            if c["cars"].get():      patch_cars(s, T("p_cars"), T, self.log)
            if c["cabins"].get():    patch_pois(s, CABINS, T("p_cabins"), T, self.log)
            if c["poi"].get():       patch_pois(s, POI_GENERIC, T("p_poi"), T, self.log)
            if c["scenic"].get():    patch_pois(s, SCENIC, T("p_scenic"), T, self.log)
            json.dump(s, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            shutil.copy(sp, sp + ".bak")
            if c["fog"].get():       patch_fog(self.var_root.get(), T, self.log)
            self.log(T("log_done")); messagebox.showinfo("", T("msg_applied"))
        except Exception as e:
            shutil.copy(bak, sp); self.log(f"✗ {e}"); messagebox.showerror("", str(e))

    def _restore(self):
        T = self.t
        if game_running(): messagebox.showwarning("", T("msg_close_restore")); return
        sp = self._save_path()
        baks = sorted(glob.glob(sp + ".patcher_*.bak"), key=os.path.getmtime)
        if not baks: messagebox.showinfo("", T("msg_no_backups")); return
        shutil.copy(baks[-1], sp); shutil.copy(baks[-1], sp + ".bak")
        self.log(f"{T('restore')}: {os.path.basename(baks[-1])}"); messagebox.showinfo("", T("msg_restored"))

if __name__ == "__main__":
    App().mainloop()
