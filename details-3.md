Absolutely—let’s wire in **dynamic color theming** so charts (bar/pie/line), tables, and accents automatically match your brand accent or a full corporate palette. Below are drop-in changes for your Python MCP server.

---

# 1) Extend the schema to allow palettes

**`models.py`**

```python
class ThemeSpec(BaseModel):
    template: str = "themes/default.potx"
    accent_color: Optional[str] = None         # "#005596"
    logo: Optional[str] = None
    footer: Optional[str] = None
    # NEW: optional full palette (primary → secondary shades)
    palette: Optional[list[str]] = None        # e.g. ["#005596","#0A77C0","#57A0D3","#86C5F4","#C3E4FD"]
    dark_mode: bool = False                    # optional: flips contrast defaults
```

---

# 2) Palette + contrast helpers

**`renderer.py`** (top-level helpers; add near other utils)

```python
from colorsys import rgb_to_hls, hls_to_rgb

def _hex_to_rgb_tuple(hex_color: str) -> tuple[int,int,int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

def _rgb_tuple_to_RGBColor(t: tuple[int,int,int]) -> RGBColor:
    r,g,b = t
    return RGBColor(r,g,b)

def _ensure_hex(h: str|None, fallback="#005596") -> str:
    if not h: return fallback
    h = h.strip()
    return h if h.startswith("#") else f"#{h}"

def _tint_shade(hex_color: str, light_delta: float) -> str:
    # light_delta in [-0.5, +0.5] (negative=shade, positive=tint)
    r,g,b = _hex_to_rgb_tuple(hex_color)
    # convert to HLS (0..1)
    h,l,s = rgb_to_hls(r/255, g/255, b/255)
    l = max(0,min(1, l + light_delta))
    r2,g2,b2 = hls_to_rgb(h,l,s)
    return f"#{int(r2*255):02X}{int(g2*255):02X}{int(b2*255):02X}"

def _derive_palette_from_accent(accent: str) -> list[str]:
    # Create 5-step palette around the accent
    return [
        _tint_shade(accent, -0.20),  # darkest
        _tint_shade(accent, -0.10),
        accent,                      # base
        _tint_shade(accent, +0.12),
        _tint_shade(accent, +0.24),  # lightest
    ]

def _get_brand_palette(spec_theme) -> list[str]:
    accent = _ensure_hex(spec_theme.accent_color, "#005596")
    if spec_theme.palette and len(spec_theme.palette) >= 2:
        return [ _ensure_hex(c) for c in spec_theme.palette ]
    return _derive_palette_from_accent(accent)

def _best_text_color(bg_hex: str, dark_mode=False) -> RGBColor:
    # Simple luminance check; dark_mode prefers lighter accents overall
    r,g,b = _hex_to_rgb_tuple(bg_hex)
    luminance = (0.2126*r + 0.7152*g + 0.0722*b) / 255
    if dark_mode:
        # prefer light text on dark backgrounds
        return RGBColor(255,255,255) if luminance < 0.7 else RGBColor(30,30,30)
    return RGBColor(30,30,30) if luminance > 0.65 else RGBColor(255,255,255)

def _pick_series_color(palette: list[str], index: int) -> RGBColor:
    return _rgb_tuple_to_RGBColor(_hex_to_rgb_tuple(palette[index % len(palette)]))
```

---

# 3) Apply palette to charts (bar, pie, line)

Update your existing `_fill_chart()` to color series/points using the palette:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

def _style_chart_colors(chart, chart_spec, palette: list[str]):
    # Legend text color (match general contrast)
    # (PowerPoint theme might override; set per-series anyway.)
    for i, series in enumerate(chart.series):
        color = _pick_series_color(palette, i)
        # Bar/column areas:
        if hasattr(series.format, "fill"):
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = color
        # Line charts:
        if hasattr(series, "format") and hasattr(series.format, "line"):
            series.format.line.color.rgb = color
        # Pie: color per-point
        if chart.chart_type == XL_CHART_TYPE.PIE:
            for j, point in enumerate(series.points):
                pcolor = _pick_series_color(palette, j)
                point.format.fill.solid()
                point.format.fill.fore_color.rgb = pcolor)

def _fill_chart(slide, chart_spec: ChartSpec, palette: list[str],
                left=Inches(1), top=Inches(2), width=Inches(8), height=Inches(4.5)):

    chart_data = CategoryChartData()
    chart_data.categories = chart_spec.categories
    for s in chart_spec.series:
        chart_data.add_series(s.name, s.values)

    chart_type_map = {
        "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "pie": XL_CHART_TYPE.PIE,
        "line": XL_CHART_TYPE.LINE
    }
    chart_type = chart_type_map.get(chart_spec.type, XL_CHART_TYPE.COLUMN_CLUSTERED)

    chart_placeholder = None
    for shape in slide.placeholders:
        if shape.is_placeholder and shape.placeholder_format.type == 3:  # CHART
            chart_placeholder = shape
            break

    if chart_placeholder:
        chart = chart_placeholder.insert_chart(chart_type, chart_data).chart
    else:
        chart_shape = slide.shapes.add_chart(chart_type, left, top, width, height, chart_data)
        chart = chart_shape.chart

    # Title and base cosmetics
    if chart_spec.title:
        chart.has_title = True
        chart.chart_title.text_frame.text = chart_spec.title
    chart.value_axis.has_major_gridlines = False if hasattr(chart, "value_axis") else None
    chart.has_legend = True
    chart.legend.include_in_layout = False

    # Apply palette
    _style_chart_colors(chart, chart_spec, palette)
```

And in your main `render_deck()` call to `_fill_chart`:

```python
palette = _get_brand_palette(spec.theme)

...

if s.chart:
    _fill_chart(slide, s.chart, palette)
```

---

# 4) Harmonize table + accents with palette

You can reuse the first color (or a darker shade) for table headers:

```python
def _fill_table(slide, table_spec: TableSpec, palette: list[str], left=Inches(1), top=Inches(2), width=Inches(8)):
    rows, cols = len(table_spec.rows) + 1, len(table_spec.columns)
    height = Inches(0.5 * rows)
    shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = shape.table

    header_bg = palette[0]  # darkest/accent
    header_text_rgb = _best_text_color(header_bg)
    header_rgb = _rgb_tuple_to_RGBColor(_hex_to_rgb_tuple(header_bg))

    # Header
    for j, col_name in enumerate(table_spec.columns):
        cell = table.cell(0, j)
        cell.text = col_name
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.color.rgb = header_text_rgb
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_rgb

    # Body
    body_text = RGBColor(40,40,40)
    for i, row in enumerate(table_spec.rows, start=1):
        for j, value in enumerate(row):
            cell = table.cell(i, j)
            cell.text = value
            cell.text_frame.paragraphs[0].font.color.rgb = body_text
```

Update the call site:

```python
if s.table:
    _fill_table(slide, s.table, palette)
```

---

# 5) Optional: dynamic header/section bars from palette

If your `.potx` doesn’t include the bar color baked-in, you can draw it:

```python
def _draw_header_bar(slide, palette: list[str]):
    bar_hex = palette[0]     # darkest/accent
    bar_rgb = _rgb_tuple_to_RGBColor(_hex_to_rgb_tuple(bar_hex))
    slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.35)
    ).fill.fore_color.rgb = bar_rgb
```

> Ideally, keep this in the **master** and not programmatic—theme fidelity is better.

---

# 6) Example: brand palette in your DeckSpec

```json
"theme": {
  "template": "themes/nice-actimize.potx",
  "accent_color": "#005596",
  "palette": ["#005596","#0A77C0","#57A0D3","#86C5F4","#C3E4FD"],
  "footer": "© NICE Actimize"
}
```

If you omit `palette`, the generator **derives** a 5-step palette from `accent_color`.

---

# 7) Summary of what you now have

* ✅ Charts (bar/pie/line) auto-colored to the brand palette
* ✅ Tables styled with brand header color + readable contrast
* ✅ Image placeholders still honored (for tight layout)
* ✅ Works with your `.potx` master to keep true corporate look

