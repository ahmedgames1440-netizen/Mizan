#!/bin/bash
# سكربت بناء تطبيق ميزان للجوال (أندرويد) — يُشغَّل على Linux أو WSL على ويندوز.
# لا يعمل على ويندوز مباشرة؛ استخدم WSL (راجع ملف README.md للتفاصيل).

set -e

echo "================================================"
echo "  بناء تطبيق ميزان للجوال (أندرويد)"
echo "================================================"

# تثبيت متطلبات النظام الأساسية
echo "[1/5] تثبيت متطلبات النظام..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git zip unzip \
    openjdk-17-jdk-headless build-essential libffi-dev libssl-dev \
    autoconf automake libtool pkg-config zlib1g-dev

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"

echo "[2/5] إنشاء بيئة افتراضية..."
python3 -m venv venv
source venv/bin/activate

echo "[3/5] تثبيت Buildozer وKivy..."
pip install --upgrade pip
pip install buildozer cython==0.29.37 kivy==2.3.1

echo "[4/5] بدء بناء APK (هذا يحمّل Android SDK/NDK لأول مرة، قد يستغرق 20-40 دقيقة ويحتاج اتصال إنترنت جيد)..."
yes | buildozer android debug

echo "[5/5] انتهى البناء."
if [ -f bin/*.apk ]; then
    echo "================================================"
    echo "  تم بناء التطبيق بنجاح! ✅"
    echo "  الملف موجود بمجلد: bin/"
    echo "================================================"
    ls -la bin/*.apk
else
    echo "[خطأ] لم يتم إيجاد ملف APK. راجع الأخطاء أعلاه."
fi
