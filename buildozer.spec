[app]
title = ميزان
package.name = mizan
package.domain = sa.mizan.app

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
source.include_patterns = assets/fonts/*.ttf,core/*.py,screens/*.py

version = 1.0

requirements = python3,kivy==2.3.1,openpyxl,reportlab,arabic-reshaper,python-bidi,plyer,pillow,numpy==v1.23.2,matplotlib==3.7.1,freetype,setuptools,cycler,python-dateutil,kiwisolver,pyparsing,six,packaging

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
