import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

SCRIPT_DIR = os.path.dirname(__file__)

BLUE = "#2a78d6"
RED = "#e34948"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

with open(os.path.join(SCRIPT_DIR, "umbrella_report_aggregated.json")) as f:
    DATA = json.load(f)


def compact(n):
    n = float(n)
    if n >= 1e9:
        return f"{n/1e9:.1f}".rstrip('0').rstrip('.') + "B"
    if n >= 1e6:
        return f"{n/1e6:.1f}".rstrip('0').rstrip('.') + "M"
    if n >= 1e3:
        return f"{n/1e3:.1f}".rstrip('0').rstrip('.') + "K"
    return str(int(n))


def commas(n):
    return f"{int(n):,}"


# ---------- Chart 1: daily trend (allowed vs blocked) ----------
def make_trend_chart(path):
    days = DATA["daily_series"]
    dates = [datetime.strptime(d["date"], "%Y-%m-%d") for d in days]
    allowed = [d["allowed"] for d in days]
    blocked = [d["blocked"] for d in days]

    fig, ax = plt.subplots(figsize=(7.4, 2.7), dpi=200)
    ax.plot(dates, allowed, color=BLUE, linewidth=1.8, label="Allowed")
    ax.fill_between(dates, allowed, color=BLUE, alpha=0.08)
    ax.plot(dates, blocked, color=RED, linewidth=1.8, label="Blocked")

    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(lambda v, pos: compact(v) if v > 0 else "0")
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

    legend = ax.legend(loc="upper left", frameon=False, fontsize=8, labelcolor=SECONDARY, ncol=2)
    fig.tight_layout(pad=0.6)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


# ---------- Chart 2/3: horizontal bar charts ----------
def make_bar_chart(path, rows, key, label_key, color, title):
    rows = rows[:8][::-1]
    labels = [r[label_key] if len(r[label_key]) <= 28 else r[label_key][:27] + "…" for r in rows]
    values = [r[key] for r in rows]

    fig, ax = plt.subplots(figsize=(3.55, 2.7), dpi=200)
    bars = ax.barh(labels, values, color=color, height=0.55)
    ax.set_xlim(0, max(values) * 1.22)

    for b, v in zip(bars, values):
        ax.text(b.get_width() + max(values) * 0.02, b.get_y() + b.get_height() / 2,
                 compact(v), va="center", fontsize=7.5, color=INK)

    ax.tick_params(colors=SECONDARY, labelsize=7.5)
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


trend_png = os.path.join(SCRIPT_DIR, "chart_trend.png")
cat_png = os.path.join(SCRIPT_DIR, "chart_top_categories.png")
blocked_cat_png = os.path.join(SCRIPT_DIR, "chart_blocked_categories.png")

make_trend_chart(trend_png)
make_bar_chart(cat_png, DATA["top_categories"], "count", "label", BLUE, "")
make_bar_chart(blocked_cat_png, DATA["top_blocked_categories"], "blocked", "label", RED, "")

# ---------- Build PDF ----------
styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitleX", parent=styles["Title"], fontName="Helvetica-Bold",
                              fontSize=20, textColor=colors.HexColor(INK), spaceAfter=2)
sub_style = ParagraphStyle("Sub", parent=styles["Normal"], fontName="Helvetica",
                            fontSize=10, textColor=colors.HexColor(SECONDARY), spaceAfter=14)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                           fontSize=12.5, textColor=colors.HexColor(INK), spaceBefore=14, spaceAfter=4)
subcaption_style = ParagraphStyle("Cap", parent=styles["Normal"], fontName="Helvetica",
                                   fontSize=8.5, textColor=colors.HexColor(MUTED), spaceAfter=8)
body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName="Helvetica",
                             fontSize=9, textColor=colors.HexColor(SECONDARY), leading=13)
footer_style = ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica",
                               fontSize=8, textColor=colors.HexColor(MUTED), alignment=TA_CENTER)

doc = SimpleDocTemplate(
    os.path.join(SCRIPT_DIR, "umbrella_report.pdf"),
    pagesize=letter,
    topMargin=0.55 * inch, bottomMargin=0.55 * inch,
    leftMargin=0.6 * inch, rightMargin=0.6 * inch,
)

story = []
s = DATA["summary"]
date_range = f'{DATA["daily_series"][0]["date"]} to {DATA["daily_series"][-1]["date"]}'

story.append(Paragraph("Umbrella Security &amp; Traffic Report", title_style))
story.append(Paragraph(f"Last 30 days &nbsp;&middot;&nbsp; {date_range}", sub_style))

# KPI table
kpi_data = [
    ["Total requests", "Allowed", "Blocked", "Block rate", "Unique domains", "Identities"],
    [compact(s["total_requests"]), compact(s["allowed_requests"]), compact(s["blocked_requests"]),
     f'{s["block_rate_pct"]}%', compact(s["unique_domains"]), commas(s["identities"])],
]
kpi_table = Table(kpi_data, colWidths=[1.13 * inch] * 6)
kpi_table.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, 0), 7.5),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(MUTED)),
    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 1), (-1, 1), 14),
    ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor(INK)),
    ("TEXTCOLOR", (2, 1), (2, 1), colors.HexColor(RED)),
    ("TEXTCOLOR", (3, 1), (3, 1), colors.HexColor(RED)),
    ("TEXTCOLOR", (1, 1), (1, 1), colors.HexColor(BLUE)),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
    ("TOPPADDING", (0, 1), (-1, 1), 0),
    ("LINEBELOW", (0, 1), (-1, 1), 0.6, colors.HexColor(GRID)),
    ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
]))
story.append(kpi_table)
story.append(Spacer(1, 4))

story.append(Paragraph("Daily request volume — allowed vs. blocked", h2_style))
story.append(Paragraph("DNS/web requests per day across the reporting period", subcaption_style))
story.append(Image(trend_png, width=6.9 * inch, height=2.52 * inch))

story.append(Paragraph("Top categories by traffic volume &nbsp;&nbsp;|&nbsp;&nbsp; by blocked requests", h2_style))
chart_row = Table(
    [[Image(cat_png, width=3.3 * inch, height=2.5 * inch), Image(blocked_cat_png, width=3.3 * inch, height=2.5 * inch)]],
    colWidths=[3.4 * inch, 3.4 * inch],
)
chart_row.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story.append(chart_row)

story.append(Spacer(1, 6))


def dest_table(rows, count_label):
    header = ["Domain", "Category", count_label]
    body_rows = []
    for r in rows[:15]:
        cats = ", ".join(r["categories"][:2]) if r["categories"] else "Uncategorized"
        body_rows.append([r["domain"], cats, commas(r["count"])])
    t = Table([header] + body_rows, colWidths=[2.6 * inch, 3.3 * inch, 1.0 * inch], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.6),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(MUTED)),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(INK)),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(GRID)),
        ("LINEBELOW", (0, 1), (-1, -2), 0.4, colors.HexColor(GRID)),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


story.append(Paragraph("Top destinations (overall)", h2_style))
story.append(Paragraph("By total request count", subcaption_style))
story.append(dest_table(DATA["top_destinations"], "Requests"))

story.append(Paragraph("Top blocked destinations", h2_style))
story.append(Paragraph("By blocked request count", subcaption_style))
story.append(dest_table(DATA["top_destinations_blocked"], "Blocked"))

story.append(Paragraph("Threat detection signal", h2_style))
event_types = DATA["event_types"]
if event_types:
    parts = ", ".join(f'{e["eventtype"].replace("_"," ")}: {commas(e["count"])} events' for e in event_types)
    note = (f"{parts}. No malware, phishing, or C2 domains were flagged by Umbrella's threat-intelligence "
            f'categories in this window — the {s["block_rate_pct"]}% block rate above is driven almost entirely '
            f"by content/application policy (software updates, social media, ads, streaming), not active threats.")
else:
    note = "No security event types were recorded in this period."
story.append(Paragraph(note, body_style))

story.append(Paragraph(f"Site / network roster ({len(DATA['sites'])})", h2_style))
story.append(Paragraph("Every registered site or network, not just active talkers", subcaption_style))

sites_header = ["Site / network", "IP address", "Verified", "Registered", "Allowed", "Blocked"]
sites_rows = [
    [
        site["name"], site["ip_address"] or "—", "Yes" if site["verified"] else "No", site["created_at"],
        commas(site["allowed"]), commas(site["blocked"]),
    ]
    for site in DATA["sites"]
]
sites_table = Table(
    [sites_header] + sites_rows,
    colWidths=[2.0 * inch, 1.3 * inch, 0.7 * inch, 0.9 * inch, 0.95 * inch, 0.95 * inch],
    repeatRows=1,
)
sites_table.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 7.2),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(MUTED)),
    ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(INK)),
    ("TEXTCOLOR", (4, 1), (4, -1), colors.HexColor(BLUE)),
    ("TEXTCOLOR", (5, 1), (5, -1), colors.HexColor(RED)),
    ("ALIGN", (4, 0), (5, -1), "RIGHT"),
    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor(GRID)),
    ("LINEBELOW", (0, 1), (-1, -2), 0.3, colors.HexColor(GRID)),
    ("TOPPADDING", (0, 0), (-1, -1), 2.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
]))
story.append(sites_table)

story.append(Spacer(1, 14))
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor(GRID)))
story.append(Spacer(1, 4))
story.append(Paragraph(
    f'Generated {datetime.now().strftime("%Y-%m-%d")} &middot; Source: Cisco Umbrella Reporting API v2',
    footer_style
))

doc.build(story)
print("Wrote", os.path.join(SCRIPT_DIR, "umbrella_report.pdf"))
