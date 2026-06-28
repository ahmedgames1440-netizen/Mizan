# -*- coding: utf-8 -*-
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

import theme
from widgets import ALabel


def build_empty_screen(message="لا توجد بيانات حتى الآن", hint="ارفع ملف نتائج للبدء"):
    box = BoxLayout(orientation="vertical", padding=dp(30), spacing=dp(10))
    box.add_widget(BoxLayout())
    box.add_widget(ALabel(text="📂", font_size="40sp", size_hint_y=None, height=dp(60),
                           halign="center"))
    box.add_widget(ALabel(text=message, font_size="15sp", bold=True,
                           size_hint_y=None, height=dp(28), halign="center"))
    box.add_widget(ALabel(text=hint, font_size="11sp",
                           color=theme.hex_to_rgba(theme.COLOR_TEXT_SECONDARY),
                           size_hint_y=None, height=dp(22), halign="center"))
    box.add_widget(BoxLayout())
    return box


def build_placeholder_screen(key):
    return build_empty_screen(message="هذه الشاشة قيد الإنشاء", hint=f"({key})")
