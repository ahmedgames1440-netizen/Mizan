# -*- coding: utf-8 -*-
"""شاشة إعدادات المدرسة الدائمة — تطبيق الجوال."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
from kivy.metrics import dp

import theme
from widgets import ALabel, AButton, Card
from core.arabic_text import ar
from core.school_settings import load_school_settings, save_school_settings


def build_settings_screen(app):
    scroll = ScrollView(size_hint=(1, 1))
    root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10), size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    saved = load_school_settings()
    state = {"logo_path": saved.get("logo_path", "")}

    card = Card(title="إعدادات المدرسة", subtitle="تُحفظ مرة واحدة وتُستخدم تلقائيًا")
    card.body.add_widget(ALabel(
        text="هذه البيانات تُملأ تلقائيًا عند تصدير أي تقرير، ويمكنك تعديلها هنا في أي وقت.",
        font_size="11sp", color=theme.hex_to_rgba(theme.COLOR_TEXT_SECONDARY),
        size_hint_y=None, height=dp(40)))

    card.body.add_widget(ALabel(text="اسم المدرسة / الإدارة", font_size="11sp",
                                  size_hint_y=None, height=dp(20)))
    school_input = TextInput(text=saved.get("school_name", ""), font_name=theme.FONT_REGULAR,
                              size_hint_y=None, height=dp(42), multiline=False,
                              halign="right", base_direction="rtl")
    card.body.add_widget(school_input)

    card.body.add_widget(ALabel(text="اسم مدير المدرسة", font_size="11sp",
                                  size_hint_y=None, height=dp(20)))
    principal_input = TextInput(text=saved.get("principal_name", ""), font_name=theme.FONT_REGULAR,
                                 size_hint_y=None, height=dp(42), multiline=False,
                                 halign="right", base_direction="rtl")
    card.body.add_widget(principal_input)

    card.body.add_widget(ALabel(text="شعار وزارة التعليم", font_size="11sp",
                                  size_hint_y=None, height=dp(20)))

    logo_preview = KivyImage(size_hint_y=None, height=dp(70))
    if state["logo_path"]:
        try:
            logo_preview.source = state["logo_path"]
        except Exception:
            pass
    card.body.add_widget(logo_preview)

    logo_status = ALabel(text=_logo_status_text(state["logo_path"]), font_size="10sp",
                          color=theme.hex_to_rgba(theme.COLOR_TEXT_MUTED),
                          size_hint_y=None, height=dp(20))
    card.body.add_widget(logo_status)

    pick_logo_btn = AButton(text="اختيار / تغيير الشعار", size_hint_y=None, height=dp(40),
                             background_color=theme.hex_to_rgba(theme.COLOR_ACCENT),
                             color=theme.hex_to_rgba("#FFFFFF"))

    def _on_logo_picked(selection):
        if selection:
            state["logo_path"] = selection[0]
            try:
                logo_preview.source = selection[0]
                logo_preview.reload()
            except Exception:
                pass
            logo_status.text = ar(_logo_status_text(state["logo_path"]))

    def _pick_logo(*_args):
        try:
            from kivy.clock import Clock
            from plyer import filechooser

            def _on_selection(selection):
                # كول-باك أندرويد يصل من خيط غير خيط Kivy — لازم تأجيله.
                Clock.schedule_once(lambda dt: _on_logo_picked(selection))

            filechooser.open_file(on_selection=_on_selection,
                                   filters=[("Images", "*.png", "*.jpg", "*.jpeg")])
        except Exception:
            import os
            from kivy.uix.filechooser import FileChooserListView
            from kivy.uix.popup import Popup
            chooser = FileChooserListView(filters=["*.png", "*.jpg", "*.jpeg"],
                                           path=os.path.expanduser("~"))
            popup = Popup(title=ar("اختر صورة الشعار"), content=chooser, size_hint=(0.9, 0.9))

            def _on_submit(instance, selection, touch):
                if selection:
                    popup.dismiss()
                    _on_logo_picked(selection)

            chooser.bind(on_submit=_on_submit)
            popup.open()

    pick_logo_btn.bind(on_release=_pick_logo)
    card.body.add_widget(pick_logo_btn)

    result_lbl = ALabel(text="", font_size="11sp", bold=True,
                         color=theme.hex_to_rgba(theme.COLOR_GREEN_FG),
                         size_hint_y=None, height=dp(0))

    def _save(*_args):
        save_school_settings(
            school_name=school_input.text,
            principal_name=principal_input.text,
            logo_path=state["logo_path"],
        )
        result_lbl.text = ar("✓ تم حفظ الإعدادات بنجاح")
        result_lbl.height = dp(26)
        app.refresh_footer()

    save_btn = AButton(text="حفظ الإعدادات", size_hint_y=None, height=dp(46),
                        background_color=theme.hex_to_rgba(theme.COLOR_ACCENT),
                        color=theme.hex_to_rgba("#FFFFFF"))
    save_btn.bind(on_release=_save)
    card.body.add_widget(save_btn)
    card.body.add_widget(result_lbl)

    root.add_widget(card)
    scroll.add_widget(root)
    return scroll


def _logo_status_text(path):
    if path:
        import os
        return os.path.basename(path)
    return "لم يتم اختيار شعار بعد"
