import tkinter as tk
from tkinter import ttk

# =====================
# Calendar Settings
# =====================
MONTHS = [
    "Fyrmont", "Glacivar", "Snowtide", "Bloomrise",
    "Verdalis", "Sunspire", "Heatfall", "Goldhaven",
    "Leafwind", "Fallowmoon", "Ironhallow", "Frostveil"
]

BASE_MONTH_LEN = {
    "Fyrmont": 42, "Glacivar": 36, "Snowtide": 30, "Bloomrise": 25,
    "Verdalis": 31, "Sunspire": 45, "Heatfall": 40, "Goldhaven": 32,
    "Leafwind": 31, "Fallowmoon": 34, "Ironhallow": 38, "Frostveil": 48
}

WEEKDAYS = ["Joviron", "Goldarix", "Flamerox", "Fironix", "Grifftor", "Pheonixday", "Sapphorex"]
WEEK_LEN = 7
FIRST_DAY_INDEX_YEAR0 = 0  # 0 = Joviron at Year 0, Day 1

# Moon
MOON_CYCLE = 30
MOON_SHIFT = 20  # Day 1 of Year 0 behaves like Moon day 21

# Colors
COLORS = {
    "bg": "#0f1320",
    "panel": "#161b2e",
    "panel_border": "#222842",
    "text": "#e9edf1",
    "muted": "#9aa5b1",
    "weekday_hdr": "#ffcf33",
    "month_hdr": "#6ec1ff",
    "cell_bg": "#131a2a",
    "cell_border": "#26324d",
    "cell_weekend": "#1e243a",
    "festival_bg": "#1b3a22",
    "festival_text": "#7ee787",
    "newyear_bg": "#3a1b2a",
    "newyear_text": "#ff7aa2",
    "moon": "#c792ea",
    "accent": "#5eead4",
}

# =====================
# Date/Calendar Logic
# =====================

def is_leap_year(year: int) -> bool:
    # Every 8th year (…, -16, -8, 0, 8, 16, …) is leap
    return year % 8 == 0

def days_in_month(year: int, month: str) -> int:
    d = BASE_MONTH_LEN[month]
    if month == "Bloomrise" and is_leap_year(year):
        d += 5  # +5 days in leap years
    return d

def year_length(year: int) -> int:
    base = sum(BASE_MONTH_LEN[m] for m in MONTHS)
    return base + (5 if is_leap_year(year) else 0)

def total_days_before_year(year: int) -> int:
    """Absolute day offset to the start of `year` relative to Year 0, Day 1 (index 0)."""
    if year == 0:
        return 0
    if year > 0:
        return sum(year_length(y) for y in range(0, year))
    else:
        return -sum(year_length(y) for y in range(year, 0))

def weekday_from_absday(abs_day_index: int) -> int:
    """abs_day_index is 0-based from Year 0, Day 1."""
    return (FIRST_DAY_INDEX_YEAR0 + abs_day_index) % WEEK_LEN

def moon_emoji(abs_day_index: int) -> str:
    phase_day = (abs_day_index + MOON_SHIFT) % MOON_CYCLE  # 0..29
    if phase_day == 0:
        return "🌑"  # New
    elif phase_day == MOON_CYCLE // 4:
        return "🌓"  # First Quarter
    elif phase_day == MOON_CYCLE // 2:
        return "🌕"  # Full
    elif phase_day == 3 * MOON_CYCLE // 4:
        return "🌗"  # Last Quarter
    return ""  # other days -> empty (you can swap to dots if you want)

def year_label(year: int) -> str:
    return f"{year} AC" if year >= 0 else f"{abs(year)} BC"

# =====================
# GUI Helpers
# =====================

def make_scrollable(root):
    """Return (outer_frame, inner_frame, canvas) with vertical scrollbar."""
    outer = ttk.Frame(root)
    outer.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer, bg=COLORS["bg"], highlightthickness=0)
    vscroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vscroll.set)

    vscroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = ttk.Frame(canvas)
    inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _on_configure(event):
        # Update scroll region
        canvas.configure(scrollregion=canvas.bbox("all"))
        # Make inner frame width match canvas width
        canvas.itemconfig(inner_id, width=event.width)

    canvas.bind("<Configure>", _on_configure)

    # Mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    return outer, inner, canvas

def style_app(root):
    root.configure(bg=COLORS["bg"])
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=COLORS["accent"])
    style.configure("MonthTitle.TLabel", font=("Segoe UI Semibold", 14), foreground=COLORS["month_hdr"])
    style.configure("WeekHdr.TLabel", font=("Segoe UI", 10, "bold"), foreground=COLORS["weekday_hdr"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])

# =====================
# Calendar Rendering
# =====================

def build_month_frame(parent, year: int, month: str, start_abs_index: int):
    """
    Create a single month mini-calendar inside `parent`.
    Returns total abs-day index after finishing the month.
    """
    # Month container
    panel = ttk.Frame(parent, style="Panel.TFrame")
    panel.grid_propagate(False)
    panel.configure(width=420, height=320)
    panel.grid()

    # Border (use a canvas for a soft border effect)
    border = tk.Canvas(panel, width=420, height=320, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["panel_border"])
    border.place(x=0, y=0)

    # Title
    ttk.Label(panel, text=month, style="MonthTitle.TLabel").place(x=12, y=8)

    # Weekday headers
    x0, y0 = 12, 40
    col_w, row_h = 45, 28
    for c, wd in enumerate(WEEKDAYS):
        ttk.Label(panel, text=wd[:3], style="WeekHdr.TLabel").place(x=x0 + c * col_w, y=y0)

    # Days grid
    days = days_in_month(year, month)
    # First day's weekday
    first_wd = weekday_from_absday(start_abs_index)
    # Draw cells
    cur_abs = start_abs_index
    r = 0
    c = first_wd

    for day in range(1, days + 1):
        cell_x = x0 + c * col_w
        cell_y = y0 + 8 + row_h * (r + 1)

        # Background / weekend / festival coloring
        wd = weekday_from_absday(cur_abs)
        bg = COLORS["cell_bg"] if wd < 5 else COLORS["cell_weekend"]

        # Festival flags
        is_newyear = (month == "Frostveil" and day == days) or (month == "Fyrmont" and day == 1)
        is_springfest = (month == "Bloomrise" and 7 <= day <= 20)

        if is_springfest:
            bg = COLORS["festival_bg"]
        if is_newyear:
            bg = COLORS["newyear_bg"]

        # Draw cell rectangle
        cell = tk.Canvas(panel, width=col_w - 4, height=row_h - 4, bg=bg, highlightthickness=1, highlightbackground=COLORS["cell_border"])
        cell.place(x=cell_x, y=cell_y)

        # Moon
        moon = moon_emoji(cur_abs)

        # Day number + moon
        num_color = COLORS["text"]
        if is_springfest:
            num_color = COLORS["festival_text"]
        elif is_newyear:
            num_color = COLORS["newyear_text"]

        cell.create_text(6, 8, anchor="w", text=f"{day}", fill=num_color, font=("Segoe UI", 10, "bold"))
        if moon:
            cell.create_text(col_w - 16, 8, anchor="e", text=moon, fill=COLORS["moon"], font=("Segoe UI", 10))

        # Event tag text
        if is_newyear:
            cell.create_text(6, 24, anchor="w", text="🎆 New Year Night", fill=COLORS["newyear_text"], font=("Segoe UI", 9))
        elif is_springfest:
            cell.create_text(6, 24, anchor="w", text="🌸 Spring Festival", fill=COLORS["festival_text"], font=("Segoe UI", 9))

        # advance
        cur_abs += 1
        c += 1
        if c == WEEK_LEN:
            c = 0
            r += 1

    return cur_abs  # first abs index after the last day of this month

def render_calendar(container, year: int):
    # Clear previous content
    for w in container.winfo_children():
        w.destroy()

    # Header
    hdr = ttk.Label(container, text=f"Year {year_label(year)}", style="Header.TLabel")
    hdr.grid(row=0, column=0, columnspan=3, pady=(10, 14))

    # Compute the absolute start-of-year day index
    abs_index = total_days_before_year(year)  # 0-based absolute index for Year X, Day 1

    # 3 columns x 4 rows grid of months
    row = 1
    col = 0
    for month in MONTHS:
        frame_holder = ttk.Frame(container, style="Panel.TFrame")
        frame_holder.grid(row=row, column=col, padx=10, pady=10, sticky="n")
        abs_index = build_month_frame(frame_holder, year, month, abs_index)

        col += 1
        if col == 3:
            col = 0
            row += 1

# =====================
# App
# =====================

def main():
    root = tk.Tk()
    root.title("Fantasy Calendar")
    root.geometry("980x720")
    style_app(root)

    # Top controls
    top = ttk.Frame(root, style="Panel.TFrame")
    top.pack(fill="x", padx=10, pady=10)

    ttk.Label(top, text="Year:", style="Panel.TLabel").pack(side="left", padx=(10, 6))
    year_var = tk.StringVar(value="0")
    entry = ttk.Entry(top, textvariable=year_var, width=10)
    entry.pack(side="left")

    def go():
        try:
            y = int(year_var.get())
        except ValueError:
            return
        render_calendar(inner, y)
        # Ensure scroll resets to top
        canvas.yview_moveto(0.0)

    ttk.Button(top, text="Show", command=go).pack(side="left", padx=10)

    # Scrollable area
    outer, inner, canvas = make_scrollable(root)

    # initial render
    render_calendar(inner, 0)

    root.mainloop()

if __name__ == "__main__":
    # expose canvas/inner to go()
    # quick workaround: define variables in outer scope after creation
    # by starting main() which closes over them
    main()
