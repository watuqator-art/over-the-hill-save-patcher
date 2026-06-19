# Over the Hill (Demo) — Save Patcher

A small GUI save editor for the **Over the Hill** demo. Pick the save folder, tick the
patches you want, hit **Apply**. An automatic backup is made before every apply, and there
is a one-click **Restore**. **Interface: English / Russian** (switcher in the window).

🇬🇧 English below · 🇷🇺 [Русская версия ниже](#-русская-версия)

➡️ **[Download the latest release](../../releases/latest)**

---

## 🇬🇧 English

### How to use
1. Download **`OverTheHillPatcher_v1.x.zip`** from [Releases](../../releases/latest) and unzip.
2. **Fully close the game** (otherwise autosave overwrites the changes).
3. Run `OverTheHillPatcher.exe` — no installation needed, it is a standalone file.
4. The save folder (`…/Documents/My Games/over the hill`) and profile are auto-detected;
   set them manually with **Browse** if needed.
5. Tick the patches → **Apply** (a backup is created automatically).
6. Launch the game and check.

### Patches
- Money → 9,999,999
- All cosmetics / accessories (134)
- All paints / liveries (199)
- All tools (×99)
- Drivable demo cars (3: Defender, FJ40_Truck, Blazer)
- Unlock all cabins (6) — start points
- Unlock all points of interest (18)
- Unlock scenic lookouts (2)
- Clear all fog of war (reveal the map)

### Notes
- **Demo build only.** Item IDs are baked into `data.json` and may differ in other builds.
- **Steam Cloud** may revert the edits on launch. If progress comes back, disable cloud
  for the demo in the game's Steam properties and apply again.
- **Restore** reverts the last backup made by the patcher.
- Antivirus may show a false positive (typical for PyInstaller builds) — the file is safe,
  and the full source is in this repository.

### Build from source
Requires Python 3:
```
pip install pyinstaller psutil customtkinter
build.bat
```
The exe appears in `dist/OverTheHillPatcher.exe`. Item data lives in `data.json` and is
bundled into the exe at build time.

### Support
💬 https://t.me/watuqator1

---

## 🇷🇺 Русская версия

Графический редактор сохранения для демо **Over the Hill**. Выбираешь папку сохранений,
отмечаешь патчи галочками, жмёшь **«Применить»**. Перед каждым применением — авто-бэкап,
есть кнопка отката. **Интерфейс: русский / английский** (переключатель в окне).

### Как пользоваться
1. Скачать **`OverTheHillPatcher_v1.x.zip`** из [Releases](../../releases/latest) и распаковать.
2. **Полностью закрыть игру** (иначе автосейв затрёт изменения).
3. Запустить `OverTheHillPatcher.exe` — установка не нужна, это автономный файл.
4. Папка сохранений (`…/Documents/My Games/over the hill`) и профиль определяются
   автоматически; при необходимости укажи вручную кнопкой **«Обзор»**.
5. Отметить патчи → **«Применить»** (бэкап создаётся сам).
6. Запустить игру и проверить.

### Патчи
- Деньги → 9 999 999
- Вся косметика / аксессуары (134)
- Все покраски / ливреи (199)
- Все инструменты (×99)
- Ездовые машины demo (3: Defender, FJ40_Truck, Blazer)
- Открыть все хижины (6) — стартовые точки
- Открыть все точки интереса (18)
- Открыть смотровые точки (2)
- Снять весь туман войны (открыть карту)

### Важно
- Поддерживается только **демо-сборка** (ID предметов зашиты в `data.json`).
- **Steam Cloud** может откатить правки — отключи облако для демо в свойствах игры в Steam.
- Кнопка **«Откат»** возвращает последний бэкап патчера.
- Антивирус может дать ложное срабатывание (особенность PyInstaller) — файл безопасен,
  исходник в этом репозитории.

### Сборка из исходника
```
pip install pyinstaller psutil customtkinter
build.bat
```

### Поддержка
💬 https://t.me/watuqator1
