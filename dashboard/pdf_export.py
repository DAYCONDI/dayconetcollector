"""PDF report generation for the DaycoNet dashboard. Pure reportlab; no Qt dependency."""

from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)


def format_bytes(n: int) -> str:
    """Format a byte count as a human-readable string with two decimals."""
    if n < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} B"
    return f"{value:.2f} {units[idx]}"


def format_speed(bps: int) -> str:
    """Format a bytes-per-second value as KB/s or MB/s."""
    if bps <= 0:
        return "0 B/s"
    if bps < 1024:
        return f"{bps} B/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.2f} KB/s"
    return f"{bps / (1024 * 1024):.2f} MB/s"


def export_report(
    path: str,
    period_name: str,
    period_label: str,
    totals: Dict[str, Any],
    breakdown: List[Dict[str, Any]],
    chart_png: Optional[bytes] = None,
    duration_seconds: int = 1,
) -> None:
    """Build a PDF report at path. Raises on write failure."""
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"DaycoNet - {period_name} Report",
        author="DaycoNet",
    )
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"DaycoNet - {period_name} Report", styles["Title"]))
    elements.append(Paragraph(period_label, styles["Normal"]))
    elements.append(Spacer(1, 5 * mm))
    data = [
        ["Sent", "Received", "Total", "Processes"],
        [
            format_bytes(totals["bytes_sent"]),
            format_bytes(totals["bytes_recv"]),
            format_bytes(totals["total_bytes"]),
            str(totals["process_count"]),
        ],
    ]
    t = Table(data, colWidths=[40 * mm, 40 * mm, 40 * mm, 40 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 5 * mm))
    if chart_png is not None and len(chart_png) > 0:
        try:
            img = Image(BytesIO(chart_png), width=180 * mm, height=80 * mm)
            img.hAlign = "CENTER"
            elements.append(img)
            elements.append(Spacer(1, 5 * mm))
        except Exception:
            pass
    if breakdown:
        header = ["Process", "Sent", "Received", "Total", "Speed"]
        rows = [header]
        for item in breakdown:
            rows.append(
                [
                    item["process_name"],
                    format_bytes(item["bytes_sent"]),
                    format_bytes(item["bytes_recv"]),
                    format_bytes(item["total_bytes"]),
                    format_speed(item.get("avg_bytes_per_sec", 0)),
                ]
            )
        bt = Table(rows, colWidths=[60 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm], repeatRows=1)
        bt.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        elements.append(bt)
        elements.append(Spacer(1, 5 * mm))
    elements.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Italic"],
        )
    )
    doc.build(elements)
