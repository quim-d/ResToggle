# ResToggle (Windows 11)

A tiny utility to quickly toggle between two display “modes” on Windows 11:
- **Work mode** (higher resolution)
- **Gaming mode** (lighter resolution and/or higher refresh rate)

The script detects the current mode and toggles to the other one, automatically picking the best compatible display mode based on your preferences.

---

## Requirements

- Windows 11
- Python 3.10+ (works on Python 3.14)
- (Optional) PyInstaller to build a `.exe`

---

## Files

- `ResToggle.py` (main script)
- `icon.ico` (optional, for an EXE with an icon)

---

## Run (as a script)

From PowerShell:

```powershell
python .\ResToggle.py
```

---

## Build an EXE with an icon (PyInstaller)

Install PyInstaller:

```powershell
python -m pip install --upgrade pip
python -m pip install pyinstaller
```

Build:

```powershell
python -m PyInstaller --clean --noconfirm --onefile --noconsole --icon ".\icon.ico" ".\ResToggle.py"
```

Output:
- `.\dist\ResToggle.exe`

---

## Quick configuration (what to edit in the code)

All tuning options are at the top of `ResToggle.py`.

### 1) Work mode (your preferred “max” resolution)

Edit `WORK_PRIORITIES` in order of preference:

```python
WORK_PRIORITIES = [
    (3840, 2400, 60),
    (2880, 1800, 120),
    (3840, 2400, None),  # None = pick the highest available Hz for that resolution
]
```

- The third value is the **refresh rate (Hz)**.
- `None` means “use the **best/maximum Hz** available for that resolution”.

### 2) Gaming mode (your preferred “min” resolution)

Edit `GAMING_PRIORITIES`:

```python
GAMING_PRIORITIES = [
    (1920, 1200, 120),
    (1920, 1200, 60),
    (1920, 1200, None),
]
```

### 3) Automatic fallback (when your priorities don’t exist)

Edit these values:

```python
GAMING_MAX_PIXELS_RATIO = 0.60
PREFER_HZ_OVER_PIXELS_IN_GAMING = True
```

What they do:
- `GAMING_MAX_PIXELS_RATIO`: in gaming fallback, the script tries to select a mode with pixel count <= this ratio of the maximum pixel count (e.g. 0.60 = 60% of max).
- `PREFER_HZ_OVER_PIXELS_IN_GAMING`: if `True`, gaming fallback prioritizes **higher Hz** before higher resolution.

---

## Hard limits (optional): min/max Hz and min/max resolution

By default, the script does **not** hard-limit refresh rate or resolution; it selects the best compatible modes it can.

If you want strict limits, add these constants near the top:

```python
HZ_MIN = 60
HZ_MAX = 120
MIN_RES = (1920, 1200)
MAX_RES = (3840, 2400)
```

Then, inside the display mode enumeration loop (the `while True:` loop where `w`, `h`, and `hz` are read), add the filters:

```python
if hz < HZ_MIN or hz > HZ_MAX:
    i += 1
    continue

if w < MIN_RES[0] or h < MIN_RES[1]:
    i += 1
    continue

if w > MAX_RES[0] or h > MAX_RES[1]:
    i += 1
    continue
```

With these filters, any display mode outside your allowed ranges is ignored.

---

## Keyboard shortcut (recommended)

1. Create a shortcut to `dist\ResToggle.exe`
2. Right-click → **Properties**
3. Set a **Shortcut key** (e.g. `Ctrl + Alt + F12`)

---

## Notes

- This script targets the **primary display** (`ChangeDisplaySettingsW`).
- For multi-monitor setups, you may prefer a version that targets a specific display using `EnumDisplayDevicesW` + `ChangeDisplaySettingsExW`.

---

## Troubleshooting

- If a specific mode won’t apply, it may not exist in your monitor/driver, or the driver refuses that exact Hz for that resolution.
- The script tries to apply the mode with an exact Hz first, and if that fails, it retries without forcing Hz so Windows can pick a valid refresh rate.
