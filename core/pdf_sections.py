# -*- coding: utf-8 -*-
"""بناء محتوى تقرير PDF — صفحة لكل قسم من أقسام البرنامج."""
import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from core.pdf_engine import (
    ar, draw_page_header, draw_page_footer, FONT_REGULAR, FONT_BOLD,
    PAGE_W, PAGE_H, MARGIN, hex_to_color,
)
from core.grade_colors import get_grade_color, grade_sort_key

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False

CONTENT_TOP = PAGE_H - 24 * mm
CONTENT_BOTTOM = 20 * mm


def _new_page(c, ctx, page_title, page_num, total_pages=None):
    draw_page_header(c, ctx, page_title)
    draw_page_footer(c, ctx, page_num, total_pages)


def _section_title(c, text, y):
    c.setFont(FONT_BOLD, 13.5)
    c.setFillColor(colors.HexColor("#1B2330"))
    c.drawRightString(PAGE_W - MARGIN, y, ar(text))
    return y - 7 * mm


def _fig_to_reader(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return ImageReader(buf)


def _kpi_row(c, items, y, theme_colors):
    """items: list of (icon_unused, value, label). يرسم 4 بطاقات KPI متجاورة."""
    n = len(items)
    gap = 4 * mm
    box_w = (PAGE_W - 2 * MARGIN - gap * (n - 1)) / n
    box_h = 22 * mm
    x = PAGE_W - MARGIN
    for value, label in items:
        x -= box_w
        c.setFillColor(colors.white)
        c.setStrokeColor(colors.HexColor("#EAEDF1"))
        c.roundRect(x, y - box_h, box_w, box_h, 2.5 * mm, fill=1, stroke=1)
        c.setFont(FONT_BOLD, 14)
        c.setFillColor(colors.HexColor("#1B2330"))
        c.drawRightString(x + box_w - 4 * mm, y - 9 * mm, ar(str(value)))
        c.setFont(FONT_REGULAR, 8)
        c.setFillColor(colors.HexColor("#6B7785"))
        c.drawRightString(x + box_w - 4 * mm, y - 16 * mm, ar(label))
        x -= gap
    return y - box_h - 8 * mm


def _table(c, headers, rows, y, col_widths=None, row_h=7 * mm, zebra=True,
           font_size=9, header_font_size=9, grade_col_index=None, raw_grades=None):
    """
    grade_col_index: رقم العمود (0-based) الذي يحتوي نص التقدير، لتلوينه تلقائيًا.
    raw_grades: قائمة بنفس طول rows فيها التقدير الخام لكل صف (لتحديد اللون الصحيح).
    """
    table_w = PAGE_W - 2 * MARGIN
    n_cols = len(headers)
    if col_widths is None:
        col_widths = [table_w / n_cols] * n_cols
    x_right = PAGE_W - MARGIN

    # header
    c.setFillColor(colors.HexColor("#0D3B2E"))
    c.rect(MARGIN, y - row_h, table_w, row_h, fill=1, stroke=0)
    c.setFont(FONT_BOLD, header_font_size)
    c.setFillColor(colors.white)
    cx = x_right
    for header, w in zip(headers, col_widths):
        c.drawCentredString(cx - w / 2, y - row_h + 2.3 * mm, ar(header))
        cx -= w
    y -= row_h

    for i, row in enumerate(rows):
        bg = colors.HexColor("#FAFBFC") if (zebra and i % 2 == 0) else colors.white
        c.setFillColor(bg)
        c.rect(MARGIN, y - row_h, table_w, row_h, fill=1, stroke=0)
        cx = x_right
        for col_idx, (val, w) in enumerate(zip(row, col_widths)):
            if grade_col_index is not None and col_idx == grade_col_index:
                raw_grade = raw_grades[i] if raw_grades else val
                c.setFont(FONT_BOLD, font_size)
                c.setFillColor(colors.HexColor(get_grade_color(raw_grade, "fg")))
            else:
                c.setFont(FONT_REGULAR, font_size)
                c.setFillColor(colors.HexColor("#1B2330"))
            c.drawCentredString(cx - w / 2, y - row_h + 2.3 * mm, ar(str(val if val is not None else "-")))
            cx -= w
        y -= row_h

    c.setStrokeColor(colors.HexColor("#E0E4E9"))
    c.setLineWidth(0.5)
    c.rect(MARGIN, y, table_w, 0, fill=0, stroke=1)
    return y


def _check_page_break(c, ctx, y, page_title, page_num_holder, min_space=30 * mm):
    if y < CONTENT_BOTTOM + min_space:
        c.showPage()
        page_num_holder[0] += 1
        _new_page(c, ctx, page_title, page_num_holder[0])
        return CONTENT_TOP
    return y


# ------------------------------------------------------------------ Dashboard
def render_dashboard_section(c, ctx, analysis, page_num_holder, first_page=True):
    page_title = "لوحة التحكم — نظرة عامة"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP

    y = _section_title(c, "لوحة التحكم", y)

    best_class = analysis.class_ranking[0][0] if analysis.class_ranking else "-"
    best_avg = analysis.class_ranking[0][1]["mean"] if analysis.class_ranking else 0
    kpis = [
        (f"{analysis.overall_average}%", "المعدل العام"),
        (str(analysis.grade_distribution.get("ممتاز", 0)), "طالب بتقدير ممتاز"),
        (f"الفصل {best_class}", f"الأعلى أداءً ({best_avg}%)"),
        (str(len(analysis.at_risk)), "طالب تحت خط الخطر"),
    ]
    y = _kpi_row(c, kpis, y, None)

    # رسمان بيانيان جنبًا بجنب: أعمدة الفصول + دونات التقديرات
    chart_h = 70 * mm
    chart_w = (PAGE_W - 2 * MARGIN - 6 * mm) / 2

    fig1, ax1 = plt.subplots(figsize=(chart_w / 25.4, chart_h / 25.4), dpi=150)
    classes_sorted = sorted(analysis.class_stats.items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    values = [v["mean"] for _, v in classes_sorted]
    bars = ax1.bar(labels, values, color="#3DBE8B", edgecolor="#0D3B2E", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 2.5, ar(f"{val}%"), ha="center", fontsize=11)
    ax1.set_ylim(0, 115)
    ax1.tick_params(labelsize=10)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_title(ar("متوسط المعدل لكل فصل"), fontsize=13)
    fig1.tight_layout()
    img1 = _fig_to_reader(fig1)

    fig2, ax2 = plt.subplots(figsize=(chart_w / 25.4, chart_h / 25.4), dpi=150)
    dist = analysis.grade_distribution
    sorted_items = sorted(dist.items(), key=lambda kv: grade_sort_key(kv[0]))
    dlabels = [k for k, _ in sorted_items]
    dvalues = [v for _, v in sorted_items]
    pcolors = [get_grade_color(l, "chart") for l in dlabels]
    wedges, _ = ax2.pie(dvalues, colors=pcolors, startangle=90,
                         wedgeprops=dict(width=0.38))
    ax2.legend(wedges, [ar(f"{l} — {v}") for l, v in zip(dlabels, dvalues)],
               loc="center", bbox_to_anchor=(0.5, -0.12), frameon=False, fontsize=11)
    ax2.set_title(ar("توزيع التقديرات"), fontsize=13)
    fig2.tight_layout()
    img2 = _fig_to_reader(fig2)

    y -= 2 * mm
    c.drawImage(img1, PAGE_W - MARGIN - chart_w, y - chart_h, width=chart_w, height=chart_h,
                preserveAspectRatio=True, anchor='n')
    c.drawImage(img2, MARGIN, y - chart_h, width=chart_w, height=chart_h,
                preserveAspectRatio=True, anchor='n')
    y -= (chart_h + 8 * mm)

    # ملاحظات
    notes = []
    if analysis.class_ranking and len(analysis.class_ranking) > 1:
        best = analysis.class_ranking[0]
        worst = analysis.class_ranking[-1]
        notes.append(f"الفصل {best[0]} يتقدم بمعدل {best[1]['mean']}% مقابل {worst[1]['mean']}% للفصل {worst[0]}")
    if analysis.weakest_subjects:
        subj, val = analysis.weakest_subjects[0]
        notes.append(f"أضعف مادة دراسياً هي {subj} بمتوسط {val}%")
    if len(analysis.at_risk) == 0:
        notes.append("لا يوجد طالب تحت خط الخطر المحدد — أداء الصف بشكل عام مطمئن")
    else:
        notes.append(f"{len(analysis.at_risk)} طالب تحت خط الخطر ويحتاجون متابعة عاجلة")

    if notes:
        y = _section_title(c, "أبرز الملاحظات", y)
        c.setFont(FONT_REGULAR, 9.5)
        c.setFillColor(colors.HexColor("#1B2330"))
        for note in notes:
            c.drawRightString(PAGE_W - MARGIN - 4 * mm, y, ar(f"•  {note}"))
            y -= 6 * mm

    return y


# ------------------------------------------------------------------ Classes
def render_classes_section(c, ctx, analysis, page_num_holder, first_page=False):
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = "مقارنة الفصول"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP
    y = _section_title(c, "مقارنة الفصول", y)

    chart_h = 75 * mm
    classes_sorted = sorted(analysis.class_stats.items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    means = [v["mean"] for _, v in classes_sorted]
    mins = [v["min"] for _, v in classes_sorted]
    maxs = [v["max"] for _, v in classes_sorted]

    fig, ax = plt.subplots(figsize=((PAGE_W - 2 * MARGIN) / 25.4, chart_h / 25.4), dpi=150)
    x = range(len(labels))
    bars = ax.bar(x, means, color="#3DBE8B", edgecolor="#0D3B2E", width=0.45, label=ar("المتوسط"))
    for bar, val in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2.5, ar(f"{val}%"), ha="center", fontsize=10)
    ax.scatter(x, maxs, color="#C8932B", zorder=5, label=ar("أعلى معدل"), s=55)
    ax.scatter(x, mins, color="#D6453D", zorder=5, label=ar("أدنى معدل"), s=55)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=11)
    ax.tick_params(labelsize=10)
    ax.set_ylim(0, 122)
    ax.legend(fontsize=11, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    img = _fig_to_reader(fig)
    c.drawImage(img, MARGIN, y - chart_h, width=PAGE_W - 2 * MARGIN, height=chart_h,
                preserveAspectRatio=True, anchor='n')
    y -= (chart_h + 10 * mm)

    y = _section_title(c, "تفاصيل كل فصل", y)
    classes_ranked = sorted(analysis.class_stats.items(), key=lambda kv: kv[1]["mean"], reverse=True)
    headers = ["عدد الطلاب", "أعلى معدل", "أدنى معدل", "المتوسط", "الفصل"]
    rows = [[s["count"], f"{s['max']}%", f"{s['min']}%", f"{s['mean']}%", f"الفصل {cl}"]
            for cl, s in classes_ranked]
    y = _table(c, headers, rows, y)
    return y


# ------------------------------------------------------------------ Subjects
def render_subjects_section(c, ctx, analysis, page_num_holder, first_page=False):
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = "تحليل المواد"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP
    y = _section_title(c, "متوسط أداء الطلاب في كل مادة", y)

    subj_avg = analysis.subject_averages_academic_only
    if subj_avg:
        items = sorted(subj_avg.items(), key=lambda kv: kv[1])
        labels = [ar(k) for k, _ in items]
        values = [v for _, v in items]
        chart_h = min(160, max(70, 6.2 * len(items))) * mm
        fig, ax = plt.subplots(figsize=((PAGE_W - 2 * MARGIN) / 25.4, chart_h / 25.4), dpi=150)
        bar_colors = ["#D6453D" if v < 65 else "#C8932B" if v < 80 else "#3DBE8B" for v in values]
        bars = ax.barh(range(len(labels)), values, color=bar_colors, height=0.55)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=11)
        ax.tick_params(axis='x', labelsize=10)
        for bar, val in zip(bars, values):
            ax.text(val + 1.8, bar.get_y() + bar.get_height() / 2, ar(f"{val}%"), va="center", fontsize=10)
        ax.set_xlim(0, 114)
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        fig.tight_layout()
        img = _fig_to_reader(fig)
        c.drawImage(img, MARGIN, y - chart_h, width=PAGE_W - 2 * MARGIN, height=chart_h,
                    preserveAspectRatio=True, anchor='n')
        y -= (chart_h + 6 * mm)
    return y


# ------------------------------------------------------------------ Watchlist
def render_watchlist_section(c, ctx, analysis, page_num_holder, first_page=False):
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = "طلاب يحتاجون دعم"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP

    if analysis.at_risk:
        y = _section_title(c, f"طلاب تحت خط الخطر ({analysis.risk_threshold}%)", y)
        headers = ["التقدير", "المعدل", "الفصل", "الاسم"]
        rows = [[s.get("general_grade") or "-", f"{s['average']}%", s.get("class") or "-", s["name_ar"]]
                for s in analysis.at_risk]
        raw_grades = [s.get("general_grade") for s in analysis.at_risk]
        col_widths = [30 * mm, 25 * mm, 20 * mm, (PAGE_W - 2 * MARGIN - 75 * mm)]
        y = _table(c, headers, rows, y, col_widths=col_widths, grade_col_index=0, raw_grades=raw_grades)
        y -= 8 * mm
    else:
        c.setFont(FONT_BOLD, 11)
        c.setFillColor(colors.HexColor("#168249"))
        c.drawRightString(PAGE_W - MARGIN, y, ar(f"لا يوجد طالب تحت خط الخطر ({analysis.risk_threshold}%) — أداء الصف مطمئن"))
        y -= 10 * mm

    page_num_holder_for_break = page_num_holder
    y = _check_page_break(c, ctx, y, page_title, page_num_holder_for_break)
    y = _section_title(c, "قائمة متابعة وقائية (أدنى 15 معدلاً)", y)
    headers = ["الغياب", "التقدير", "المعدل", "الفصل", "الاسم"]
    rows = [[s.get("absence") or 0, s.get("general_grade") or "-", f"{s['average']}%",
             s.get("class") or "-", s["name_ar"]]
            for s in analysis.watch_list]
    raw_grades = [s.get("general_grade") for s in analysis.watch_list]
    col_widths = [20 * mm, 30 * mm, 25 * mm, 20 * mm, (PAGE_W - 2 * MARGIN - 95 * mm)]
    y = _table(c, headers, rows, y, col_widths=col_widths, grade_col_index=1, raw_grades=raw_grades)
    return y


# ------------------------------------------------------------------ Anomalies
def render_anomalies_section(c, ctx, analysis, page_num_holder, first_page=False):
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = "حالات شاذة"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP

    y = _section_title(c, "كشف الحالات الشاذة", y)
    c.setFont(FONT_REGULAR, 9)
    c.setFillColor(colors.HexColor("#6B7785"))
    desc = "طلاب بتفاوت كبير وغير متوقع بمادة معينة مقارنة بمتوسط أدائهم الشخصي بباقي المواد"
    c.drawRightString(PAGE_W - MARGIN, y, ar(desc))
    y -= 10 * mm

    anomalies = analysis.anomalies[:20]
    if not anomalies:
        c.setFont(FONT_BOLD, 11)
        c.setFillColor(colors.HexColor("#168249"))
        c.drawRightString(PAGE_W - MARGIN, y, ar("لم يتم رصد أي حالات شاذة لافتة — أداء الطلاب متسق عبر موادهم"))
        return y - 10 * mm

    headers = ["الاتجاه", "الفرق", "متوسطه الشخصي", "درجة المادة", "المادة", "الفصل", "الاسم"]
    rows = []
    for a in anomalies:
        s = a["student"]
        direction_text = "ضعف لافت" if a["direction"] == "drop" else "تميّز لافت"
        rows.append([direction_text, f"{a['gap']:+.1f}", f"{a['personal_avg']}%",
                     f"{a['subject_pct']}%", a["subject"], s.get("class") or "-", s["name_ar"]])

    name_w = PAGE_W - 2 * MARGIN - (22 + 18 + 24 + 22 + 30 + 16) * mm
    col_widths = [22 * mm, 18 * mm, 24 * mm, 22 * mm, 30 * mm, 16 * mm, name_w]
    y = _table(c, headers, rows, y, col_widths=col_widths, row_h=6.5 * mm, font_size=8.5)
    return y


# ------------------------------------------------------------------ Teacher subject report
def render_teacher_subject_report(c, ctx, analysis, subject_name, page_num_holder, first_page=False):
    """يبني تقريرًا مخصصًا لمادة دراسية واحدة: متوسطات، توزيع تقديرات، وأضعف الطلاب بها."""
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    report = analysis.subject_report(subject_name)
    page_title = f"تقرير مادة {subject_name}"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP

    if report is None:
        y = _section_title(c, page_title, y)
        c.setFont(FONT_REGULAR, 10)
        c.setFillColor(colors.HexColor("#6B7785"))
        c.drawRightString(PAGE_W - MARGIN, y, ar("لا توجد بيانات لهذه المادة"))
        return y

    y = _section_title(c, f"تقرير مادة: {subject_name}", y)

    kpis = [
        (f"{report['overall_avg']}%", "المتوسط العام"),
        (f"{report['highest']}%", "أعلى درجة"),
        (f"{report['lowest']}%", "أدنى درجة"),
        (str(report["count"]), "عدد الطلاب"),
    ]
    y = _kpi_row(c, kpis, y, None)
    y -= 2 * mm

    chart_w = (PAGE_W - 2 * MARGIN - 6 * mm) / 2
    chart_h = 68 * mm

    fig1, ax1 = plt.subplots(figsize=(chart_w / 25.4, chart_h / 25.4), dpi=150)
    classes_sorted = sorted(report["class_stats"].items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    values = [v["mean"] for _, v in classes_sorted]
    bars = ax1.bar(labels, values, color="#3DBE8B", edgecolor="#0D3B2E", linewidth=0.8)
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 2, ar(f"{val}%"), ha="center", fontsize=10)
    ax1.set_ylim(0, 112)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_title(ar("متوسط المادة لكل فصل"), fontsize=11)
    fig1.tight_layout()
    img1 = _fig_to_reader(fig1)

    fig2, ax2 = plt.subplots(figsize=(chart_w / 25.4, chart_h / 25.4), dpi=150)
    dist = report["grade_distribution"]
    sorted_items = sorted(dist.items(), key=lambda kv: grade_sort_key(kv[0]))
    dlabels = [k for k, _ in sorted_items]
    dvalues = [v for _, v in sorted_items]
    pcolors = [get_grade_color(l, "chart") for l in dlabels]
    wedges, _ = ax2.pie(dvalues, colors=pcolors, startangle=90, wedgeprops=dict(width=0.38))
    ax2.legend(wedges, [ar(f"{l} — {v}") for l, v in zip(dlabels, dvalues)],
               loc="center", bbox_to_anchor=(0.5, -0.12), frameon=False, fontsize=10)
    ax2.set_title(ar("توزيع التقديرات"), fontsize=11)
    fig2.tight_layout()
    img2 = _fig_to_reader(fig2)

    c.drawImage(img1, PAGE_W - MARGIN - chart_w, y - chart_h, width=chart_w, height=chart_h,
                preserveAspectRatio=True, anchor='n')
    c.drawImage(img2, MARGIN, y - chart_h, width=chart_w, height=chart_h,
                preserveAspectRatio=True, anchor='n')
    y -= (chart_h + 10 * mm)

    y = _check_page_break(c, ctx, y, page_title, page_num_holder, min_space=70 * mm)
    y = _section_title(c, "أضعف 5 طلاب بهذه المادة", y)
    headers = ["التقدير", "الدرجة", "الفصل", "الاسم"]
    rows = [[r["grade_label"] or "-", f"{r['pct']}%", r["student"].get("class") or "-", r["student"]["name_ar"]]
            for r in report["weakest"]]
    raw_grades = [r["grade_label"] for r in report["weakest"]]
    col_widths = [30 * mm, 25 * mm, 20 * mm, (PAGE_W - 2 * MARGIN - 75 * mm)]
    y = _table(c, headers, rows, y, col_widths=col_widths, grade_col_index=0, raw_grades=raw_grades)

    return y


# ------------------------------------------------------------------ Students
def render_students_section(c, ctx, analysis, page_num_holder, first_page=False):
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = "بيانات جميع الطلاب"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP
    y = _section_title(c, f"بيانات جميع الطلاب ({analysis.count} طالب)", y)

    headers = ["الغياب", "ترتيب الفصل", "ترتيب الصف", "التقدير", "المعدل", "الفصل", "الاسم"]
    name_w = PAGE_W - 2 * MARGIN - (20 + 25 + 25 + 25 + 20 + 18) * mm
    col_widths = [20 * mm, 25 * mm, 25 * mm, 25 * mm, 20 * mm, 18 * mm, name_w]

    rows_per_page = 26
    all_rows = analysis.student_table_rows()
    i = 0
    while i < len(all_rows):
        chunk = all_rows[i:i + rows_per_page]
        rows = [[r["الغياب"] if r["الغياب"] is not None else "-",
                 r["ترتيب الفصل"] or "-", r["ترتيب الصف"] or "-",
                 r["التقدير"] or "-", f"{r['المعدل']}%", r["الفصل"] or "-", r["الاسم"]]
                for r in chunk]
        raw_grades = [r["التقدير"] for r in chunk]
        y = _table(c, headers, rows, y, col_widths=col_widths, row_h=6.3 * mm, font_size=8.3,
                   grade_col_index=3, raw_grades=raw_grades)
        i += rows_per_page
        if i < len(all_rows):
            c.showPage()
            page_num_holder[0] += 1
            _new_page(c, ctx, page_title, page_num_holder[0])
            y = CONTENT_TOP
    return y


# ------------------------------------------------------------------ Individual student report
NON_ACADEMIC_SUBJECTS_PDF = {"المواظبة", "السلوك", "النشاط"}


def render_single_student_page(c, ctx, analysis, student, page_num_holder, first_page=False):
    """يرسم صفحة واحدة كاملة لطالب محدد: بياناته، درجاته بكل مادة، ومقارنته بمتوسط فصله."""
    if not first_page:
        c.showPage()
        page_num_holder[0] += 1
    page_title = f"تقرير الطالب — {student['name_ar']}"
    _new_page(c, ctx, page_title, page_num_holder[0])
    y = CONTENT_TOP

    y = _section_title(c, student["name_ar"], y)
    c.setFont(FONT_REGULAR, 9.5)
    c.setFillColor(colors.HexColor("#6B7785"))
    meta_line = f"الفصل {student.get('class') or '-'}   —   الهوية: {student.get('id') or '-'}"
    c.drawRightString(PAGE_W - MARGIN, y, ar(meta_line))
    y -= 10 * mm

    cls = student.get("class")
    class_mean = analysis.class_stats.get(cls, {}).get("mean") if cls in analysis.class_stats else None
    kpis = [
        (f"{student.get('average', '-')}%", "المعدل العام"),
        (student.get("general_grade") or "-", "التقدير"),
        (student.get("rank_in_class") or "-", "ترتيب الفصل"),
        (f"{class_mean}%" if class_mean is not None else "-", "متوسط الفصل"),
    ]
    y = _kpi_row(c, kpis, y, None)
    y -= 2 * mm

    # رسم بياني: درجة الطالب بكل مادة مقارنة بمتوسط الفصل لنفس المادة
    subjects = [s for s in student.get("subjects", [])
                if s.get("total_pct") is not None and s["subject_ar"] not in NON_ACADEMIC_SUBJECTS_PDF]

    if subjects:
        subj_class_avg = {}
        for other in analysis.students:
            if other.get("class") != cls:
                continue
            for sub in other.get("subjects", []):
                if sub.get("total_pct") is not None and sub["subject_ar"] not in NON_ACADEMIC_SUBJECTS_PDF:
                    subj_class_avg.setdefault(sub["subject_ar"], []).append(sub["total_pct"])

        labels = [ar(s["subject_ar"]) for s in subjects]
        student_vals = [s["total_pct"] for s in subjects]
        class_vals = [
            round(sum(subj_class_avg.get(s["subject_ar"], [0])) / max(len(subj_class_avg.get(s["subject_ar"], [1])), 1), 1)
            for s in subjects
        ]

        chart_h = min(95, max(55, 5.5 * len(subjects))) * mm
        fig, ax = plt.subplots(figsize=((PAGE_W - 2 * MARGIN) / 25.4, chart_h / 25.4), dpi=150)
        y_pos = range(len(labels))
        bar_h = 0.35
        ax.barh([p + bar_h / 2 for p in y_pos], student_vals, height=bar_h,
                color="#3DBE8B", label=ar("الطالب"))
        ax.barh([p - bar_h / 2 for p in y_pos], class_vals, height=bar_h,
                color="#C8E6D6", label=ar("متوسط الفصل"))
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, 112)
        ax.legend(fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.1), ncol=2)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis='both', labelsize=8)
        fig.tight_layout()
        img = _fig_to_reader(fig)
        c.drawImage(img, MARGIN, y - chart_h, width=PAGE_W - 2 * MARGIN, height=chart_h,
                    preserveAspectRatio=True, anchor='n')
        y -= (chart_h + 7 * mm)

    y = _check_page_break(c, ctx, y, page_title, page_num_holder, min_space=80 * mm)

    # جدول الدرجات التفصيلي
    y = _section_title(c, "الدرجات التفصيلية", y)
    headers = ["التقدير", "النسبة", "المادة"]
    rows = [[s.get("grade_label") or "-", f"{s['total_pct']}%", s["subject_ar"]]
            for s in subjects]
    raw_grades = [s.get("grade_label") for s in subjects]
    col_widths = [35 * mm, 30 * mm, (PAGE_W - 2 * MARGIN - 65 * mm)]
    y = _table(c, headers, rows, y, col_widths=col_widths, row_h=6 * mm, font_size=8.5, header_font_size=9,
               grade_col_index=0, raw_grades=raw_grades)
    y -= 6 * mm

    # ملاحظات تلقائية
    notes = analysis.student_insight(student)
    if notes:
        y = _check_page_break(c, ctx, y, page_title, page_num_holder, min_space=35 * mm)
        y = _section_title(c, "ملاحظات", y)
        c.setFont(FONT_REGULAR, 9.5)
        c.setFillColor(colors.HexColor("#1B2330"))
        for note in notes:
            c.drawRightString(PAGE_W - MARGIN - 4 * mm, y, ar(f"•  {note}"))
            y -= 6 * mm

    return y
