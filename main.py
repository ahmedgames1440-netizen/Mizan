# -*- coding: utf-8 -*-
"""تطبيق ميزان للجوال — نقطة التشغيل الرئيسية."""
import os
from kivy.config import Config
Config.set("graphics", "width", "412")
Config.set("graphics", "height", "869")

from kivy.app import App
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.properties import BooleanProperty

import theme
from widgets import ALabel, AButton, ColoredBoxLayout
from core.arabic_text import ar


def _resource_path(relative_path):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


LabelBase.register(
    name=theme.FONT_REGULAR,
    fn_regular=_resource_path("assets/fonts/NotoSansArabic-Regular.ttf"),
    fn_bold=_resource_path("assets/fonts/NotoSansArabic-Bold.ttf"),
)
LabelBase.register(
    name=theme.FONT_BOLD,
    fn_regular=_resource_path("assets/fonts/NotoSansArabic-Bold.ttf"),
)

NAV_ITEMS = [
    ("home", "⌂", "الرئيسية"),
    ("classes", "▤", "مقارنة الفصول"),
    ("subjects", "▥", "تحليل المواد"),
    ("watchlist", "⚠", "طلاب يحتاجون دعم"),
    ("anomalies", "◬", "حالات شاذة"),
    ("teacher_report", "▥", "تقرير المعلم"),
    ("comparison", "▤", "مقارنة فصلين"),
    ("students", "▤", "بيانات الطلاب"),
    ("settings", "⚙", "إعدادات المدرسة"),
]


class NavDrawer(ColoredBoxLayout):
    """قائمة تنقّل جانبية منزلقة (Drawer) — بديل الشريط الجانبي بنسخة سطح المكتب."""
    def __init__(self, on_nav, **kwargs):
        super().__init__(bg_hex=theme.COLOR_SIDEBAR_BG, orientation="vertical",
                          padding=dp(16), spacing=dp(4), **kwargs)
        self.on_nav = on_nav
        self.nav_buttons = {}

        brand = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(50))
        brand.add_widget(ALabel(text="ميزان", font_size="20sp", bold=True,
                                 color=theme.hex_to_rgba("#FFFFFF")))
        self.add_widget(brand)
        self.add_widget(ALabel(text="تحليل نتائج الطلاب", font_size="11sp",
                                color=theme.hex_to_rgba(theme.COLOR_SIDEBAR_TEXT_MUTED),
                                size_hint_y=None, height=dp(24)))
        self.add_widget(BoxLayout(size_hint_y=None, height=dp(12)))

        scroll = ScrollView(size_hint=(1, 1))
        nav_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        nav_box.bind(minimum_height=nav_box.setter("height"))

        for key, icon, label in NAV_ITEMS:
            btn = self._make_nav_button(key, icon, label)
            nav_box.add_widget(btn)
            self.nav_buttons[key] = btn

        scroll.add_widget(nav_box)
        self.add_widget(scroll)

        self.footer_label = ALabel(text="لم يتم رفع ملف بعد", font_size="10sp",
                                    color=theme.hex_to_rgba(theme.COLOR_SIDEBAR_TEXT_MUTED),
                                    size_hint_y=None, height=dp(40))
        self.add_widget(self.footer_label)

    def _make_nav_button(self, key, icon, label, active=False):
        bg = theme.COLOR_ACCENT if active else theme.COLOR_SIDEBAR_BG
        fg = "#FFFFFF" if active else theme.COLOR_SIDEBAR_TEXT
        btn_box = ColoredBoxLayout(bg_hex=bg, radius=dp(8), orientation="horizontal",
                                    size_hint_y=None, height=dp(44), padding=(dp(10), 0))
        lbl = ALabel(text=f"{label}  {icon}", font_size="13sp",
                      color=theme.hex_to_rgba(fg))
        btn_box.add_widget(lbl)
        btn_box._key = key
        btn_box._label_widget = lbl
        btn_box.bind(on_touch_up=lambda inst, touch: self._handle_touch(inst, touch, key))
        return btn_box

    def _handle_touch(self, inst, touch, key):
        if inst.collide_point(*touch.pos):
            self.on_nav(key)

    def set_active(self, active_key):
        for key, btn in self.nav_buttons.items():
            is_active = key == active_key
            bg = theme.COLOR_ACCENT if is_active else theme.COLOR_SIDEBAR_BG
            fg = "#FFFFFF" if is_active else theme.COLOR_SIDEBAR_TEXT
            btn.set_bg(bg)
            btn._label_widget.color = theme.hex_to_rgba(fg)

    def update_footer(self, text):
        self.footer_label.text = ar(text)


class RootWidget(FloatLayout):
    """
    الحاوية الجذرية: تحتوي ScreenManager بالخلفية + NavDrawer منزلق من اليمين
    + شريط علوي بزر القائمة. هذا النمط (Drawer) هو المعادل الجوّالي للشريط
    الجانبي الثابت بنسخة سطح المكتب.
    """
    drawer_open = BooleanProperty(False)

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        self.sm = ScreenManager(transition=SlideTransition(direction="left"))
        self.add_widget(self.sm)

        self.topbar = ColoredBoxLayout(
            bg_hex=theme.COLOR_BG, orientation="horizontal",
            size_hint=(1, None), height=dp(56),
            pos_hint={"top": 1}, padding=(dp(8), 0),
        )
        self.menu_btn = AButton(text="☰", font_size="20sp", size_hint=(None, None),
                                  size=(dp(44), dp(44)),
                                  background_color=theme.hex_to_rgba(theme.COLOR_BG),
                                  color=theme.hex_to_rgba(theme.COLOR_TEXT_PRIMARY))
        self.menu_btn.bind(on_release=lambda *a: self.toggle_drawer())
        self.title_lbl = ALabel(text="ميزان", font_size="15sp", bold=True)
        self.topbar.add_widget(self.menu_btn)
        self.topbar.add_widget(self.title_lbl)
        self.add_widget(self.topbar)

        self.drawer = NavDrawer(on_nav=self.app.switch_screen,
                                 size_hint=(None, 1), width=dp(260),
                                 pos_hint={"right": -0.001, "top": 1})

        self.scrim = ColoredBoxLayout(bg_hex="#000000", size_hint=(1, 1), opacity=0)
        self.scrim.bind(on_touch_up=lambda inst, touch: self.close_drawer()
                          if inst.collide_point(*touch.pos) and self.drawer_open else None)
        self.add_widget(self.scrim)
        self.add_widget(self.drawer)

    def toggle_drawer(self):
        if self.drawer_open:
            self.close_drawer()
        else:
            self.open_drawer()

    def open_drawer(self):
        self.drawer_open = True
        self.scrim.opacity = 0.01
        Animation(opacity=0.5, duration=0.18).start(self.scrim)
        Animation(pos_hint={"right": 1, "top": 1}, duration=0.22, t="out_cubic").start(self.drawer)

    def close_drawer(self):
        Animation(opacity=0, duration=0.15).start(self.scrim)
        Animation(pos_hint={"right": -0.001, "top": 1}, duration=0.2, t="in_cubic").start(self.drawer)
        self.drawer_open = False


class MizanMobileApp(App):
    def build(self):
        Window.clearcolor = theme.hex_to_rgba(theme.COLOR_BG)
        self.analysis = None
        self.current_filepath = None
        self.comparison = None
        self.current_screen_key = "home"

        self.root_widget = RootWidget(self)
        self._register_screens()
        self.switch_screen("home")
        return self.root_widget

    def _register_screens(self):
        from screens.home_screen import build_home_screen
        from screens.classes_screen import build_classes_screen
        from screens.subjects_screen import build_subjects_screen
        from screens.watchlist_screen import build_watchlist_screen
        from screens.anomalies_screen import build_anomalies_screen
        from screens.teacher_report_screen import build_teacher_report_screen
        from screens.comparison_screen import build_comparison_screen
        from screens.students_screen import build_students_screen
        from screens.settings_screen import build_settings_screen

        self._screen_builders = {
            "home": build_home_screen,
            "classes": build_classes_screen,
            "subjects": build_subjects_screen,
            "watchlist": build_watchlist_screen,
            "anomalies": build_anomalies_screen,
            "teacher_report": build_teacher_report_screen,
            "comparison": build_comparison_screen,
            "students": build_students_screen,
            "settings": build_settings_screen,
        }
        # شاشة فاضية مبدئية لكل المفاتيح الأخرى لحين بناء كل شاشة بدورها
        for key, _, _ in NAV_ITEMS:
            screen = Screen(name=key)
            self.root_widget.sm.add_widget(screen)

    def switch_screen(self, key):
        self.current_screen_key = key
        self.root_widget.drawer.set_active(key)
        self.root_widget.close_drawer()

        titles = dict((k, label) for k, _, label in NAV_ITEMS)
        self.root_widget.title_lbl.text = ar(titles.get(key, "ميزان"))

        screen = self.root_widget.sm.get_screen(key)
        screen.clear_widgets()

        builder = self._screen_builders.get(key)
        if builder:
            content = builder(self)
        else:
            from screens.empty_screen import build_placeholder_screen
            content = build_placeholder_screen(key)
        screen.add_widget(content)
        self.root_widget.sm.current = key

    def refresh_footer(self):
        if self.analysis is not None and self.current_filepath:
            filename = os.path.basename(self.current_filepath)
            short = filename if len(filename) <= 26 else filename[:23] + "..."
            self.root_widget.drawer.update_footer(f"⛁ {short}\n{self.analysis.count} طالب")
        else:
            self.root_widget.drawer.update_footer("لم يتم رفع ملف بعد")


if __name__ == "__main__":
    MizanMobileApp().run()
