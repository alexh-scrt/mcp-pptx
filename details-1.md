✅ **Image Placeholder Filling**
✅ **TABLE layout example**

Here’s the additional code to drop into the same `renderer.py` module (or add as `renderer_extensions.py`):

---

### 🔹 1. Image Placeholder Filling

Add this utility function before `render_deck()`:

```python
def _fill_image_placeholders(slide, images: list[ImageSpec]):
    """
    Fill any picture placeholders (not arbitrary shapes) in the layout.
    This preserves the design grid in .potx master.
    """
    if not images:
        return
    for idx, shape in enumerate(slide.placeholders):
        if not shape.is_placeholder:
            continue
        phf = shape.placeholder_format
        # type 18 = PICTURE
        if phf.type == 18 and idx < len(images):
            img = images[idx]
            path = fetch_asset(img.src)
            shape.insert_picture(str(path))
```

Then, inside `render_deck()` (where we create each slide), **replace** this part:

```python
if s.images:
    placement = s.images[0].placement if s.images else "right"
    _insert_images(slide, s.images, placement)
```

with this:

```python
if s.images:
    # Try placeholder first; if none, use fallback placement logic
    try:
        _fill_image_placeholders(slide, s.images)
    except Exception:
        placement = s.images[0].placement if s.images else "right"
        _insert_images(slide, s.images, placement)
```

This allows your branded `.potx` to control image position and size via **placeholders**, rather than manual inches-based coordinates.

---

### 🔹 2. Table Layout Example

Add this function:

```python
def _fill_table(slide, table_spec: TableSpec, left=Inches(1), top=Inches(2), width=Inches(8)):
    """
    Add a table with headers and rows to a slide.
    """
    rows, cols = len(table_spec.rows) + 1, len(table_spec.columns)
    height = Inches(0.5 * rows)
    shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = shape.table

    # Header row
    for j, col_name in enumerate(table_spec.columns):
        cell = table.cell(0, j)
        cell.text = col_name
        cell.text_frame.paragraphs[0].font.bold = True
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0, 85, 150)
        cell.text_frame.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)

    # Data rows
    for i, row in enumerate(table_spec.rows, start=1):
        for j, value in enumerate(row):
            table.cell(i, j).text = value
```

Now in `render_deck()` add:

```python
if s.table:
    _fill_table(slide, s.table)
```

---

### 🔹 3. Example SlideSpec for Table

Add this to your `nice_actimize_deck.json` after other slides:

```json
{
  "layout": "TABLE",
  "title": "Operational Efficiency Metrics",
  "subtitle": "Performance KPIs across financial crime domains",
  "table": {
    "columns": ["Metric", "Before NICE", "After NICE", "Improvement"],
    "rows": [
      ["Alert Triage Time", "10 hrs", "2 hrs", "80% faster"],
      ["False Positives", "100%", "40%", "↓ 60%"],
      ["Case Resolution Rate", "55%", "85%", "+30 pts"]
    ]
  }
}
```

---

### ✅ Result

Now your generator will:

* Detect and fill picture placeholders directly in `.potx` templates.
* Add professional tables with headers, colors, and layout.
* Maintain brand design (header bar, logo, footer, etc.).

