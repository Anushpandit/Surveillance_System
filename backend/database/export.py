"""CSV and PDF incident-report generation."""

import csv
import io
from datetime import datetime

from fpdf import FPDF

from backend.database.models import EventModel


def generate_csv(events: list[EventModel]) -> bytes:
    """Generate a UTF-8 CSV report for persisted events."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "event_type", "label", "confidence", "timestamp", "source", "reviewed", "false_positive"]
    )
    for event in events:
        writer.writerow(
            [
                event.id,
                event.event_type,
                event.label or "",
                f"{event.confidence:.3f}",
                event.timestamp.isoformat() if event.timestamp else "",
                event.source,
                event.reviewed,
                event.is_false_positive,
            ]
        )
    return output.getvalue().encode("utf-8")


def generate_pdf(
    events: list[EventModel],
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> bytes:
    """Generate a compact page-break-safe PDF incident report."""

    pdf = FPDF(orientation="landscape", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Surveillance Incident Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", size=9)
    period = f"{start_date or 'beginning'} to {end_date or 'now'}"
    pdf.cell(0, 7, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Period: {period}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    headers = ["ID", "Type", "Confidence", "Timestamp", "Source", "Status"]
    widths = [14, 28, 24, 48, 120, 38]
    pdf.set_font("Helvetica", "B", 9)
    for header, width in zip(headers, widths):
        pdf.cell(width, 8, header, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", size=8)
    for event in events:
        values = [
            str(event.id),
            event.event_type,
            f"{event.confidence:.3f}",
            event.timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.timestamp else "",
            event.source[:70],
            "False positive" if event.is_false_positive else ("Reviewed" if event.reviewed else "Unreviewed"),
        ]
        for value, width in zip(values, widths):
            pdf.cell(width, 7, value, border=1)
        pdf.ln()
    return bytes(pdf.output())
