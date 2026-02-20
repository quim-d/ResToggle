import ctypes
from ctypes import wintypes

# Preferencias (incluyo 2880x1800 por si tu "1880" era 1800; no molesta si no existe)
WORK_PRIORITIES = [
    (3840, 2400, 60),
    (2880, 1880, 120),
    (2880, 1800, 120),
    (3840, 2400, None),  # None = mejor Hz disponible para esa resolución
    (2880, 1880, None),
    (2880, 1800, None),
]

GAMING_PRIORITIES = [
    (1920, 1200, 120),
    (1920, 1200, 60),
    (1920, 1200, None),
]

# Fallback gaming: intenta quedarse por debajo de este ratio de píxeles del modo máximo
GAMING_MAX_PIXELS_RATIO = 0.60
PREFER_HZ_OVER_PIXELS_IN_GAMING = True

ENUM_CURRENT_SETTINGS = -1
CDS_UPDATEREGISTRY = 0x01

DISP_CHANGE_SUCCESSFUL = 0

DM_PELSWIDTH = 0x00080000
DM_PELSHEIGHT = 0x00100000
DM_DISPLAYFREQUENCY = 0x00400000


class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmOrientation", wintypes.SHORT),
        ("dmPaperSize", wintypes.SHORT),
        ("dmPaperLength", wintypes.SHORT),
        ("dmPaperWidth", wintypes.SHORT),
        ("dmScale", wintypes.SHORT),
        ("dmCopies", wintypes.SHORT),
        ("dmDefaultSource", wintypes.SHORT),
        ("dmPrintQuality", wintypes.SHORT),
        ("dmColor", wintypes.SHORT),
        ("dmDuplex", wintypes.SHORT),
        ("dmYResolution", wintypes.SHORT),
        ("dmTTOption", wintypes.SHORT),
        ("dmCollate", wintypes.SHORT),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


user32 = ctypes.WinDLL("user32", use_last_error=True)

EnumDisplaySettingsW = user32.EnumDisplaySettingsW
EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DEVMODEW)]
EnumDisplaySettingsW.restype = wintypes.BOOL

ChangeDisplaySettingsW = user32.ChangeDisplaySettingsW
ChangeDisplaySettingsW.argtypes = [ctypes.POINTER(DEVMODEW), wintypes.DWORD]
ChangeDisplaySettingsW.restype = wintypes.LONG


def msgbox_error(text: str, title: str = "Display Toggle") -> None:
    ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)


def get_current_mode() -> tuple[int, int, int]:
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if not EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        raise OSError("EnumDisplaySettingsW(ENUM_CURRENT_SETTINGS) failed")
    return int(dm.dmPelsWidth), int(dm.dmPelsHeight), int(dm.dmDisplayFrequency)


def apply_mode(w: int, h: int, hz: int | None) -> bool:
    dm = DEVMODEW()
    dm.dmSize = ctypes.sizeof(DEVMODEW)
    if not EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return False

    dm.dmPelsWidth = w
    dm.dmPelsHeight = h

    if hz is None:
        dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT
    else:
        dm.dmDisplayFrequency = hz
        dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT | DM_DISPLAYFREQUENCY

    res = ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
    return res == DISP_CHANGE_SUCCESSFUL


def pick_from_priorities(best_for_res: dict[tuple[int, int], int], exact_set: set[tuple[int, int, int]],
                         priorities: list[tuple[int, int, int | None]],
                         best_global: tuple[int, int, int]) -> tuple[int, int, int]:
    for w, h, hz in priorities:
        if hz is None:
            found_hz = best_for_res.get((w, h))
            if found_hz:
                return (w, h, found_hz)
        else:
            if (w, h, hz) in exact_set:
                return (w, h, hz)
    return best_global


def main() -> int:
    try:
        cur_w, cur_h, cur_hz = get_current_mode()

        # Enumeración rápida: una pasada, sin sort, sin dedupe costoso
        dm = DEVMODEW()
        dm.dmSize = ctypes.sizeof(DEVMODEW)

        exact_set: set[tuple[int, int, int]] = set()
        best_for_res: dict[tuple[int, int], int] = {}  # (w,h)->max hz

        best_global = (cur_w, cur_h, max(cur_hz, 1))
        best_global_pixels = cur_w * cur_h

        all_modes: list[tuple[int, int, int, int]] = []  # (w,h,hz,pixels)
        max_pixels = best_global_pixels

        i = 0
        while True:
            if not EnumDisplaySettingsW(None, i, ctypes.byref(dm)):
                break

            w = int(dm.dmPelsWidth)
            h = int(dm.dmPelsHeight)
            hz = int(dm.dmDisplayFrequency)

            if w <= 0 or h <= 0 or hz <= 0:
                i += 1
                continue

            pixels = w * h

            exact_set.add((w, h, hz))

            prev_hz = best_for_res.get((w, h))
            if prev_hz is None or hz > prev_hz:
                best_for_res[(w, h)] = hz

            if pixels > best_global_pixels or (pixels == best_global_pixels and hz > best_global[2]):
                best_global = (w, h, hz)
                best_global_pixels = pixels

            if pixels > max_pixels:
                max_pixels = pixels

            all_modes.append((w, h, hz, pixels))
            i += 1

        if not all_modes:
            msgbox_error("No he podido listar modos de pantalla disponibles.")
            return 1

        # Elegir work
        work_mode = pick_from_priorities(best_for_res, exact_set, WORK_PRIORITIES, best_global)

        # Elegir gaming
        gaming_mode = pick_from_priorities(best_for_res, exact_set, GAMING_PRIORITIES, best_global)

        # Si gaming aún es best_global (o algo raro), aplica fallback gaming “alto Hz, píxeles contenidos”
        if gaming_mode == best_global:
            threshold = int(max_pixels * GAMING_MAX_PIXELS_RATIO)
            pool = [m for m in all_modes if m[3] <= threshold] or all_modes

            if PREFER_HZ_OVER_PIXELS_IN_GAMING:
                # Max Hz, y si empata, más píxeles (mejor nitidez manteniendo Hz)
                w, h, hz, _ = max(pool, key=lambda m: (m[2], m[3]))
            else:
                # Max píxeles, y si empata, más Hz
                w, h, hz, _ = max(pool, key=lambda m: (m[3], m[2]))

            gaming_mode = (w, h, hz)

        # Toggle: si estás en resolución "work", vuelve a gaming; si no, vete a work
        if (cur_w, cur_h) == (work_mode[0], work_mode[1]):
            target = gaming_mode
        else:
            target = work_mode

        # Aplicar rápido: primero con Hz exacto; si falla, reintento sin fijar Hz
        ok = apply_mode(target[0], target[1], target[2])
        if not ok:
            ok2 = apply_mode(target[0], target[1], None)
            if not ok2:
                msgbox_error(
                    f"Error aplicando: {target[0]}x{target[1]} @{target[2]}Hz.\n"
                    "El driver puede no aceptar ese modo exacto."
                )
                return 2

        return 0

    except Exception as e:
        msgbox_error(f"Error inesperado:\n\n{e}")
        return 99


if __name__ == "__main__":
    raise SystemExit(main())