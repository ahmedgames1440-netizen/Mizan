# -*- coding: utf-8 -*-
"""أدوات مساعدة خاصة بأندرويد. os.path.expanduser('~') على أندرويد يرجع
مجلد خاص بالتطبيق فاضي من ملفات المستخدم، فمنتقي الملفات الاحتياطي
(FileChooserListView) يحتاج مسار حقيقي للتخزين المشترك ليجد ملفات Excel."""
import os


def default_filechooser_path():
    try:
        from android.storage import primary_external_storage_path
        path = primary_external_storage_path()
        if path and os.path.isdir(path):
            return path
    except Exception:
        pass
    return os.path.expanduser("~")
