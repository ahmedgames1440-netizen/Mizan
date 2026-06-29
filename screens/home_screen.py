# -*- coding: utf-8 -*-
"""شاشة الرئيسية (لوحة التحكم) — تطبيق الجوال."""
import io
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.metrics import dp

from core.optional_deps import plt, HAS_CHARTS

import theme
from widgets import ALabel, AButton, Card, KPICard, safe_chart_widget
from core.arabic_text import ar
from core.grade_colors import get_grade_color, grade_sort_key
from core.parser import parse_grades_file, FORMAT_UNKNOWN
from core.analysis import AnalysisResult


def _fig_to_kivy_image(fig, **kwargs):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=theme.COLOR_CARD_BG, transparent=False)
    plt.close(fig)
    buf.seek(0)
    core_img = CoreImage(buf, ext="png")
    return KivyImage(texture=core_img.texture, **kwargs)


def build_home_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10),
                      size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    upload_btn = AButton(
        text="رفع ملف نتائج  ⛁", size_hint_y=None, height=dp(46),
        background_color=theme.hex_to_rgba(theme.COLOR_ACCENT),
        color=theme.hex_to_rgba("#FFFFFF"), font_size="14sp",
    )
    upload_btn.bind(on_release=lambda *a: _pick_file(app, scroll))
    root.add_widget(upload_btn)

    if app.analysis is not None:
        export_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        report_btn = AButton(text="تصدير تقرير شامل  ▤", font_size="12sp",
                              background_color=theme.hex_to_rgba(theme.COLOR_CARD_BG),
                              color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY))
        report_btn.bind(on_release=lambda *a: _export_full_report(app))
        cert_btn = AButton(text="شهادات تكريم  ★", font_size="12sp",
                            background_color=theme.hex_to_rgba(theme.COLOR_CARD_BG),
                            color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY))
        cert_btn.bind(on_release=lambda *a: _export_certificates(app))
        export_row.add_widget(report_btn)
        export_row.add_widget(cert_btn)
        root.add_widget(export_row)

    if app.analysis is None:
        from screens.empty_screen import build_empty_screen
        root.add_widget(build_empty_screen())
        scroll.add_widget(root)
        return scroll

    analysis = app.analysis

    kpi_grid = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    best_class = analysis.class_ranking[0][0] if analysis.class_ranking else "-"
    best_avg = analysis.class_ranking[0][1]["mean"] if analysis.class_ranking else 0
    kpi_grid.add_widget(KPICard(f"{analysis.overall_average}%", "المعدل العام", palette="green"))
    kpi_grid.add_widget(KPICard(str(len(analysis.at_risk)), "تحت خط الخطر", palette="red"))
    root.add_widget(kpi_grid)

    kpi_grid2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(80), spacing=dp(8))
    kpi_grid2.add_widget(KPICard(str(analysis.grade_distribution.get("ممتاز", 0)), "طالب ممتاز", palette="blue"))
    kpi_grid2.add_widget(KPICard(f"الفصل {best_class}", f"الأعلى ({best_avg}%)", palette="gold"))
    root.add_widget(kpi_grid2)

    chart_card = Card(title="متوسط المعدل لكل فصل")
    chart_img = safe_chart_widget(_build_class_chart_image, analysis)
    chart_img.size_hint_y = None
    chart_img.height = dp(200)
    chart_card.body.add_widget(chart_img)
    root.add_widget(chart_card)

    donut_card = Card(title="توزيع التقديرات")
    donut_img = safe_chart_widget(_build_grade_donut_image, analysis)
    donut_img.size_hint_y = None
    donut_img.height = dp(220)
    donut_card.body.add_widget(donut_img)
    root.add_widget(donut_card)

    notes_card = Card(title="أبرز الملاحظات")
    for note in _build_notes(analysis):
        lbl = ALabel(text=f"•  {note}", font_size="12sp", size_hint_y=None, height=dp(36))
        notes_card.body.add_widget(lbl)
    root.add_widget(notes_card)

    scroll.add_widget(root)
    return scroll


def _build_class_chart_image(analysis):
    classes_sorted = sorted(analysis.class_stats.items(), key=lambda kv: str(kv[0]))
    labels = [ar(f"الفصل {cl}") for cl, _ in classes_sorted]
    values = [v["mean"] for _, v in classes_sorted]

    fig, ax = plt.subplots(figsize=(5.6, 3.2), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    ax.set_facecolor(theme.COLOR_CARD_BG)
    bars = ax.bar(labels, values, color=theme.COLOR_CHART_GREEN_LIGHT, width=0.5,
                   edgecolor=theme.COLOR_CHART_GREEN_DARK, linewidth=0.8)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2, ar(f"{val}%"),
                ha="center", fontsize=11)
    ax.set_ylim(0, 115)
    ax.tick_params(labelsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)


def _build_grade_donut_image(analysis):
    dist = analysis.grade_distribution
    sorted_items = sorted(dist.items(), key=lambda kv: grade_sort_key(kv[0]))
    labels = [k for k, _ in sorted_items]
    values = [v for _, v in sorted_items]
    colors_palette = [get_grade_color(l, "chart") for l in labels]

    fig, ax = plt.subplots(figsize=(4.2, 4.6), dpi=120)
    fig.patch.set_facecolor(theme.COLOR_CARD_BG)
    wedges, _ = ax.pie(values, colors=colors_palette, startangle=90,
                        wedgeprops=dict(width=0.38, edgecolor=theme.COLOR_CARD_BG))
    ax.legend(wedges, [ar(f"{l} — {v}") for l, v in zip(labels, values)],
              loc="center", bbox_to_anchor=(0.5, -0.12), frameon=False, fontsize=11)
    fig.tight_layout()
    return _fig_to_kivy_image(fig, allow_stretch=True, keep_ratio=True)


def _build_notes(analysis):
    notes = []
    if analysis.class_ranking and len(analysis.class_ranking) > 1:
        best = analysis.class_ranking[0]
        worst = analysis.class_ranking[-1]
        notes.append(f"الفصل {best[0]} يتقدم بمعدل {best[1]['mean']}% مقابل {worst[1]['mean']}% للفصل {worst[0]}")
    if analysis.weakest_subjects:
        subj, val = analysis.weakest_subjects[0]
        notes.append(f"أضعف مادة دراسياً هي {subj} بمتوسط {val}%")
    if len(analysis.at_risk) == 0:
        notes.append("لا يوجد طالب تحت خط الخطر — أداء الصف مطمئن")
    else:
        notes.append(f"{len(analysis.at_risk)} طالب تحت خط الخطر ويحتاجون متابعة عاجلة")
    return notes


def _pick_file(app, scroll_ref):
    """يفتح منتقي ملفات (متوافق مع أندرويد عبر plyer، مع احتياط لسطح المكتب)."""
    try:
        from kivy.clock import Clock
        from plyer import filechooser

        def _on_selection(selection):
            # يصل هذا الكول-باك من خيط نظام أندرويد، لا خيط Kivy — يجب
            # تأجيل أي كود يلمس الواجهة لخيط Kivy الرئيسي وإلا يفشل بصمت.
            if selection:
                Clock.schedule_once(lambda dt: _process_file(app, selection[0]))

        filechooser.open_file(
            on_selection=_on_selection,
            filters=[("Excel files", "*.xlsx", "*.xls")],
        )
    except Exception:
        import traceback
        traceback.print_exc()
        # احتياط بيئة سطح المكتب/الاختبار: نافذة Kivy الأصلية لاختيار الملفات
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.popup import Popup

        from core.android_utils import default_filechooser_path
        chooser = FileChooserListView(filters=["*.xlsx", "*.xls"], path=default_filechooser_path())
        popup = Popup(title="اختر ملف نتائج", content=chooser, size_hint=(0.9, 0.9))

        def _on_submit(instance, selection, touch):
            if selection:
                popup.dismiss()
                _process_file(app, selection[0])

        chooser.bind(on_submit=_on_submit)
        popup.open()


def _process_file(app, filepath):
    if not os.path.isfile(filepath):
        _show_error(
            "تعذّر الوصول للملف. هذا يحصل عادة لو صلاحية "
            "\"الوصول لجميع الملفات\" غير مفعّلة لتطبيق ميزان.\n\n"
            "فعّلها من: إعدادات الجهاز ← التطبيقات ← ميزان ← الأذونات "
            "← الوصول إلى كل الملفات."
        )
        return
    try:
        students, fmt = parse_grades_file(filepath)
    except PermissionError as e:
        _show_error(
            "لا توجد صلاحية كافية لقراءة هذا الملف.\n\n"
            "فعّل صلاحية \"الوصول لجميع الملفات\" من: إعدادات الجهاز ← "
            "التطبيقات ← ميزان ← الأذونات، ثم أعد المحاولة."
        )
        return
    except Exception as e:
        _show_error(f"تعذّر قراءة الملف:\n{e}")
        return

    if fmt == FORMAT_UNKNOWN or not students:
        _show_error("تعذّر التعرف على صيغة الملف. تأكد أنه مُصدَّر من نظام نور.")
        return

    app.analysis = AnalysisResult(students, risk_threshold=65.0)
    app.current_filepath = filepath
    app.refresh_footer()
    app.switch_screen("home")


def _show_error(message):
    from kivy.uix.popup import Popup
    popup = Popup(title=ar("خطأ"), content=ALabel(text=message, font_size="13sp"),
                   size_hint=(0.85, 0.4))
    popup.open()



def _get_report_context(app):
    from core.pdf_engine import ReportContext
    from core.school_settings import load_school_settings
    settings = load_school_settings()
    grade_title = ""
    if app.current_filepath:
        raw_name = os.path.splitext(os.path.basename(app.current_filepath))[0]
        grade_title = raw_name.replace("_", " ").strip()
    return ReportContext(
        school_name=settings.get("school_name", ""),
        grade_title=grade_title,
        principal_name=settings.get("principal_name", ""),
        logo_path=settings.get("logo_path") or None,
    )


def _output_dir(app):
    try:
        return app.user_data_dir
    except Exception:
        return os.path.expanduser("~")


def _export_full_report(app):
    from core.optional_deps import HAS_PDF, UNAVAILABLE_PDF_MESSAGE
    if not HAS_PDF:
        _show_error(UNAVAILABLE_PDF_MESSAGE)
        return
    ctx = _get_report_context(app)
    out_path = os.path.join(_output_dir(app), "تقرير_شامل.pdf")
    try:
        from core.pdf_report import export_full_report
        export_full_report(out_path, ctx, app.analysis)
        _show_success(f"تم حفظ التقرير الشامل:\n{out_path}")
    except Exception as e:
        _show_error(f"تعذّر إنشاء التقرير:\n{e}")


def _export_certificates(app):
    from core.optional_deps import HAS_PDF, UNAVAILABLE_PDF_MESSAGE
    if not HAS_PDF:
        _show_error(UNAVAILABLE_PDF_MESSAGE)
        return
    ctx = _get_report_context(app)
    out_path = os.path.join(_output_dir(app), "شهادات_التكريم.pdf")
    try:
        from core.certificates import export_top_students_certificates
        export_top_students_certificates(out_path, ctx, app.analysis, top_n=3, scope="class")
        _show_success(f"تم حفظ شهادات التكريم:\n{out_path}")
    except Exception as e:
        _show_error(f"تعذّر إنشاء الشهادات:\n{e}")


def _show_success(message):
    from kivy.uix.popup import Popup
    popup = Popup(title=ar("تم بنجاح"), content=ALabel(text=message, font_size="12sp"),
                   size_hint=(0.85, 0.35))
    popup.open()
