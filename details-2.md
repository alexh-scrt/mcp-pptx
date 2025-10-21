We’ll teach the MCP server to detect chart placeholders in `.potx` layouts and auto-populate them with bar or pie charts from JSON data arrays.

---

## 🔹 Step 1 — Extend the Data Model

Add a `ChartSpec` model to **`models.py`**.

```python
from typing import Literal, List, Optional

ChartType = Literal["bar", "pie", "line"]

class ChartSeries(BaseModel):
    name: str
    values: List[float]

class ChartSpec(BaseModel):
    title: Optional[str] = None
    type: ChartType = "bar"
    categories: List[str]
    series: List[ChartSeries]
```

And extend the `SlideSpec`:

```python
class SlideSpec(BaseModel):
    ...
    chart: Optional[ChartSpec] = None
```

---

## 🔹 Step 2 — Add Chart Rendering Logic

In **`renderer.py`**, import:

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
```

Add a helper below `_fill_table()`:

```python
def _fill_chart(slide, chart_spec: ChartSpec, left=Inches(1), top=Inches(2), width=Inches(8), height=Inches(4.5)):
    """
    Create a bar/pie/line chart directly on a slide.
    If the layout includes a chart placeholder, we can insert there instead.
    """
    chart_data = CategoryChartData()
    chart_data.categories = chart_spec.categories

    for s in chart_spec.series:
        chart_data.add_series(s.name, s.values)

    # Pick chart type
    chart_type_map = {
        "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "pie": XL_CHART_TYPE.PIE,
        "line": XL_CHART_TYPE.LINE
    }
    chart_type = chart_type_map.get(chart_spec.type, XL_CHART_TYPE.COLUMN_CLUSTERED)

    # Try placeholder first
    chart_placeholder = None
    for shape in slide.placeholders:
        if shape.is_placeholder and shape.placeholder_format.type == 3:  # type 3 = CHART
            chart_placeholder = shape
            break

    if chart_placeholder:
        chart = chart_placeholder.insert_chart(chart_type, chart_data).chart
    else:
        chart_shape = slide.shapes.add_chart(chart_type, left, top, width, height, chart_data)
        chart = chart_shape.chart

    # Optional styling
    if chart_spec.title:
        chart.has_title = True
        chart.chart_title.text_frame.text = chart_spec.title
    chart.value_axis.has_major_gridlines = False
    chart.has_legend = True
    chart.legend.include_in_layout = False
```

And in `render_deck()` (after table section):

```python
if s.chart:
    _fill_chart(slide, s.chart)
```

---

## 🔹 Step 3 — Example SlideSpec (Chart)

Add this to your deck JSON:

```json
{
  "layout": "IMAGE_FOCUS",
  "title": "Fraud Detection Improvement",
  "subtitle": "Reduction in False Positives (Pre- vs Post-Implementation)",
  "chart": {
    "title": "False Positives Reduction",
    "type": "bar",
    "categories": ["Q1", "Q2", "Q3", "Q4"],
    "series": [
      { "name": "Before X-Sight", "values": [100, 90, 85, 80] },
      { "name": "After X-Sight", "values": [60, 50, 45, 40] }
    ]
  }
}
```

For a pie chart:

```json
{
  "layout": "TABLE",
  "title": "Case Resolution by Type",
  "chart": {
    "title": "Case Breakdown",
    "type": "pie",
    "categories": ["Fraud", "AML", "Sanctions", "Compliance"],
    "series": [{ "name": "Resolved Cases", "values": [45, 30, 15, 10] }]
  }
}
```

---

## 🔹 Step 4 — Placeholder Integration

If your `.potx` theme has **chart placeholders**, `_fill_chart()` will populate them automatically, preserving layout.
To create one in PowerPoint:

1. Open **View → Slide Master**
2. Choose a layout (e.g., “Chart Layout”)
3. Insert → Chart → any type
4. Delete the chart’s sample data but **keep the placeholder frame**
5. Save as `.potx` and rename the layout to `CHART_LAYOUT`

The renderer will detect this and use it.

---

## 🔹 Step 5 — Run It

You can now include in your DeckSpec slides of type `"CHART_LAYOUT"` or `"IMAGE_FOCUS"` with `chart` defined, and the MCP server will render a properly styled, data-driven chart.

---

### ✅ Summary

Your Python MCP PowerPoint generator now supports:

| Feature                      | Status |
| ---------------------------- | ------ |
| Text, bullets, titles        | ✅      |
| Image placeholders           | ✅      |
| Tables                       | ✅      |
| Charts (bar, pie, line)      | ✅      |
| Real `.potx` themes          | ✅      |
| Fully JSON-driven generation | ✅      |

---

