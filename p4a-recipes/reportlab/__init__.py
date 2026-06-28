import os
import shutil
import sh

from pythonforandroid.logger import info
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.util import current_directory, ensure_dir, touch


class ReportLabRecipe(CompiledComponentsPythonRecipe):
    """
    نسخة محلية من recipe ريبورت لاب الأصلي في python-for-android، بفرق واحد:
    تحذف مصدر مسرّع C (_rl_accel) قبل البناء. هذا المسرّع يستخدم Unicode C API
    قديم (PyUnicode_GET_SIZE/AS_UNICODE) أُزيل من بايثون 3.12+، فيفشل تجميعه
    على Android. ريبورت لاب مصمم للعمل بدونه (fallback بايثون خالص تلقائيًا)،
    فحذفه آمن ولا يغيّر أي سلوك ظاهر للمستخدم — فقط أبطأ بنسبة ضئيلة.
    """
    version = 'fe660f227cac'
    url = 'https://hg.reportlab.com/hg-public/reportlab/archive/{version}.tar.gz'
    depends = ['freetype']
    call_hostpython_via_targetpython = False

    def prebuild_arch(self, arch):
        if not self.is_patched(arch):
            super().prebuild_arch(arch)
            recipe_dir = self.get_build_dir(arch.arch)

            font_dir = os.path.join(recipe_dir, "src", "reportlab", "fonts")
            if os.path.exists(font_dir):
                for file in os.listdir(font_dir):
                    if file.lower().startswith('darkgarden'):
                        os.remove(os.path.join(font_dir, file))

            self.apply_patch('patches/fix-setup.patch', arch.arch)
            touch(os.path.join(recipe_dir, '.patched'))
            ft = self.get_recipe('freetype', self.ctx)
            ft_dir = ft.get_build_dir(arch.arch)
            ft_lib_dir = os.environ.get('_FT_LIB_', os.path.join(ft_dir, 'objs', '.libs'))
            ft_inc_dir = os.environ.get('_FT_INC_', os.path.join(ft_dir, 'include'))
            tmp_dir = os.path.normpath(os.path.join(recipe_dir, "..", "..", "tmp"))
            info('reportlab recipe: recipe_dir={}'.format(recipe_dir))
            info('reportlab recipe: tmp_dir={}'.format(tmp_dir))
            info('reportlab recipe: ft_dir={}'.format(ft_dir))
            info('reportlab recipe: ft_lib_dir={}'.format(ft_lib_dir))
            info('reportlab recipe: ft_inc_dir={}'.format(ft_inc_dir))
            with current_directory(recipe_dir):
                ensure_dir(tmp_dir)
                pfbfile = os.path.join(tmp_dir, "pfbfer-20070710.zip")
                if not os.path.isfile(pfbfile):
                    sh.wget("http://www.reportlab.com/ftp/pfbfer-20070710.zip", "-O", pfbfile)
                sh.unzip("-u", "-d", os.path.join(recipe_dir, "src", "reportlab", "fonts"), pfbfile)
                if os.path.isfile("setup.py"):
                    with open('setup.py', 'r') as f:
                        text = f.read().replace('_FT_LIB_', ft_lib_dir).replace('_FT_INC_', ft_inc_dir)
                    with open('setup.py', 'w') as f:
                        f.write(text)

            # يعطّل امتدادات C القديمة (rl_accel, renderPM) لأنها لا تبني على
            # بايثون 3.12+/أندرويد (تستخدم Unicode C API أُزيل من بايثون).
            # كلاهما اختياري وريبورت لاب يرجع تلقائيًا لتنفيذ بايثون خالص بدونهما.
            # renderPM غير مستخدم بالتطبيق أصلًا (لا تحويل رسومات لصور raster).
            for ext_dirname in ("rl_accel", "renderPM"):
                ext_dir = os.path.join(recipe_dir, "src", "rl_addons", ext_dirname)
                if os.path.isdir(ext_dir):
                    shutil.rmtree(ext_dir)
                    info('reportlab recipe: removed {} C source (incompatible with modern Python C API)'.format(ext_dirname))

    def build_compiled_components(self, arch):
        # بدون rl_accel/renderPM ما عاد فيه أي C extension يُبنى؛ setup.py build_ext
        # ما عاد يُنشئ مجلد build/lib.* أصلًا، والكود الأصلي بـ p4a يفترض وجوده
        # دائمًا فيفشل بـ IndexError. نتجاوز خطوة بناء الإكستنشن بالكامل.
        info('reportlab recipe: no C extensions left to build, skipping build_ext')


recipe = ReportLabRecipe()
