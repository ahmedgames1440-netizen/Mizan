# -*- coding: utf-8 -*-
"""
إعدادات المدرسة الدائمة (اسم المدرسة، اسم المدير، الشعار).
تُحفظ مرة واحدة وتُستخدم تلقائيًا في كل تصدير تقرير، دون الحاجة لإعادة كتابتها.

ملاحظة جوال: يستخدم مجلد بيانات التطبيق الخاص بـ Kivy (App.user_data_dir)
بدل مجلد المستخدم العادي، لأن أندرويد يفرض مساحة تخزين خاصة بكل تطبيق.
"""
import os
import json
import shutil


def _get_storage_dir():
    """يرجع مجلد بيانات التطبيق الصحيح حسب المنصة (أندرويد أو سطح المكتب)."""
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            return app.user_data_dir
    except Exception:
        pass
    # احتياطي: وضع تطوير/اختبار على سطح المكتب بدون تطبيق Kivy شغّال
    fallback = os.path.join(os.path.expanduser("~"), ".mizan_mobile_data")
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _settings_path():
    return os.path.join(_get_storage_dir(), "school_settings.json")


def _logo_storage_dir():
    d = os.path.join(_get_storage_dir(), "assets")
    os.makedirs(d, exist_ok=True)
    return d


DEFAULTS = {
    "school_name": "",
    "principal_name": "",
    "logo_path": "",
}


def load_school_settings():
    """يرجع قاموس إعدادات المدرسة المحفوظة، أو القيم الافتراضية الفاضية."""
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULTS)
        merged.update({k: v for k, v in data.items() if k in DEFAULTS})
        return merged
    except Exception:
        return dict(DEFAULTS)


def save_school_settings(school_name="", principal_name="", logo_path=""):
    """
    يحفظ إعدادات المدرسة بشكل دائم. لو تم تمرير مسار شعار جديد، يتم نسخه
    لمجلد ثابت تابع للبرنامج حتى لا يُفقد لو المستخدم نقل/حذف الملف الأصلي.
    """
    stored_logo_path = logo_path
    if logo_path and os.path.exists(logo_path):
        stored_logo_path = _persist_logo_file(logo_path)

    data = {
        "school_name": school_name.strip(),
        "principal_name": principal_name.strip(),
        "logo_path": stored_logo_path or "",
    }
    try:
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass
    return data


def _persist_logo_file(source_path):
    """ينسخ ملف الشعار لمجلد دائم تابع للبرنامج، ويرجع المسار الجديد."""
    try:
        dest_dir = _logo_storage_dir()
        ext = os.path.splitext(source_path)[1] or ".png"
        dest_path = os.path.join(dest_dir, f"school_logo{ext}")
        if os.path.abspath(source_path) != os.path.abspath(dest_path):
            shutil.copyfile(source_path, dest_path)
        return dest_path
    except Exception:
        return source_path


def has_saved_settings():
    s = load_school_settings()
    return bool(s.get("school_name") or s.get("logo_path"))


def clear_school_settings():
    try:
        os.remove(_settings_path())
    except Exception:
        pass
