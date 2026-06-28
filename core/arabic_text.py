# -*- coding: utf-8 -*-
"""
معالجة النص العربي لعرضه بشكل صحيح ومتصل داخل Kivy.
بعكس Tkinter على Windows، Kivy لا يملك أي دعم RTL مدمج على أي نظام تشغيل
(حتى على أندرويد نفسه) — لذلك هذي المعالجة مطلوبة دومًا وبدون أي استثناء،
على عكس core/arabic_text.py في نسخة سطح المكتب.
"""
import arabic_reshaper
from bidi.algorithm import get_display

_reshaper = arabic_reshaper.ArabicReshaper({
    "delete_harakat": True,
    "support_ligatures": True,
})


def ar(text):
    """يحوّل نص عربي/مختلط إلى شكل متصل وبترتيب عرض صحيح لعرضه بـ Kivy Label/Button."""
    if text is None:
        return ""
    text = str(text)
    try:
        reshaped = _reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text
