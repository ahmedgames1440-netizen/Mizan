# -*- coding: utf-8 -*-
"""
استيراد آمن للمكتبات الاختيارية الثقيلة (matplotlib, reportlab) التي قد لا
تكون مدعومة على بعض المنصات — تحديدًا iOS حاليًا، حيث matplotlib وnumpy
ليس لهما recipe رسمي مستقر في kivy-ios (مشاكل بناء/ربط معروفة وغير محلولة
في مستودع kivy-ios الرسمي وقت كتابة هذا الكود).

بدون هذا العزل، أي `import matplotlib` أو `import reportlab` على مستوى
الملف يفشل بالكامل (ImportError) ويكسر استيراد كل شاشة تعتمد عليه، حتى لو
الميزة المعطوبة (رسم بياني أو PDF) ليست هي المطلوبة فعليًا في تلك اللحظة.

الاستخدام في باقي الكود:
    from core.optional_deps import plt, HAS_CHARTS
    from core.optional_deps import rl_canvas, A4, mm, colors, HAS_PDF

ثم التحقق من HAS_CHARTS / HAS_PDF قبل استخدام الميزة، أو الاعتماد على
safe_chart_widget بـ widgets.py الذي يتحقق من ذلك تلقائيًا.
"""

# ---------- matplotlib ----------
HAS_CHARTS = True
plt = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: F401
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False
except Exception:
    HAS_CHARTS = False
    plt = None


# ---------- reportlab ----------
HAS_PDF = True
rl_canvas = None
A4 = None
landscape = None
mm = None
colors = None
ImageReader = None
pdfmetrics = None
TTFont = None
try:
    from reportlab.pdfgen import canvas as rl_canvas  # noqa: F401
    from reportlab.lib.pagesizes import A4, landscape  # noqa: F401
    from reportlab.lib.units import mm  # noqa: F401
    from reportlab.lib import colors  # noqa: F401
    from reportlab.lib.utils import ImageReader  # noqa: F401
    from reportlab.pdfbase import pdfmetrics  # noqa: F401
    from reportlab.pdfbase.ttfonts import TTFont  # noqa: F401
except Exception:
    HAS_PDF = False
    rl_canvas = None
    A4 = None
    landscape = None
    mm = None
    colors = None
    ImageReader = None
    pdfmetrics = None
    TTFont = None


UNAVAILABLE_CHARTS_MESSAGE = "الرسوم البيانية غير متوفرة على هذا الإصدار حاليًا."
UNAVAILABLE_PDF_MESSAGE = "تصدير PDF غير متوفر على هذا الإصدار حاليًا."
