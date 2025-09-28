import urllib.parse
import logging
from typing import List, Tuple
import subprocess

# ================================
# 📜 تنظیمات لاگ‌گیری
# ================================
# این بخش مسئول ذخیره‌سازی لاگ‌ها در فایل است تا در صورت بروز خطا یا نیاز به بررسی روند اجرای کد،
# اطلاعات دقیقی در اختیار داشته باشیم.
logging.basicConfig(
    filename="update.log",               # نام فایل لاگ
    level=logging.INFO,                  # سطح لاگ (INFO = پیام‌های عمومی + خطاها)
    format="%(asctime)s - %(levelname)s - %(message)s",  # فرمت نمایش لاگ
    encoding="utf-8"                     # پشتیبانی از زبان فارسی
)


# ================================
# 🏗️ کلاس پردازش کانفیگ‌ها
# ================================
class ConfigProcessor:
    """
    این کلاس مسئول پردازش فایل‌های لیست URL و تولید فایل‌های نهایی کانفیگ بر اساس یک قالب (Template) است.
    """





    def __init__(self):
        # مسیر فایل‌های ورودی و خروجی
        self.template_path = "mihomo_template.txt"    # فایل قالب اصلی
        self.output_dir = "Sublist"                   # پوشه خروجی برای ذخیره فایل‌ها
        self.readme_path = "README.md"                # فایل راهنما (خروجی Markdown)

        # لیست‌های ورودی
        self.simple_list = "Simple_URL_List.txt"      # لیست ساده شامل URLهای مستقیم
        self.complex_list = "Complex_URL_list.txt"    # لیست پیچیده شامل URLهایی که نیاز به پردازش دارند

        # Dynamically detect repo URL
        self.base_url = self._detect_repo_url()

    def _detect_repo_url(self) -> str:
        """
        Detects the GitHub repository URL of the current project.
        Falls back to default if detection fails.
        """
        try:
            # Run `git remote get-url origin` to fetch repo URL
            repo_url = subprocess.check_output(
                ["git", "remote", "get-url", "origin"], 
                stderr=subprocess.DEVNULL
            ).decode().strip()

            # Example: git@github.com:user/repo.git OR https://github.com/user/repo.git
            if repo_url.startswith("git@"):
                # Convert SSH form -> https://github.com/user/repo
                repo_url = repo_url.replace(":", "/").replace("git@", "https://")
            if repo_url.endswith(".git"):
                repo_url = repo_url[:-4]

            # Build raw content base URL
            return repo_url.replace("https://github.com", "https://raw.githubusercontent.com") + "/main/Sublist/"
        except Exception:
            # Fallback default
            return "https://raw.githubusercontent.com/10ium/MihomoSaz/main/Sublist/"
    
    # ================================
    # 🔗 پردازش URL
    # ================================
    def _process_url(self, url: str, is_complex: bool) -> str:
        """
        پردازش URL بر اساس نوع لیست:
        - اگر ساده باشد همان URL بازگردانده می‌شود.
        - اگر پیچیده باشد، URL رمزگذاری (Encoding) شده و در یک قالب API خاص قرار می‌گیرد.
        """
        if is_complex:
            encoded = urllib.parse.quote(url, safe=':/?&=')  # رمزگذاری URL با حفظ برخی کاراکترهای خاص
            return (
                "https://url.v1.mk/sub?&url="
                f"{encoded}&target=clash&config="
@@ -37,123 +87,160 @@ def _process_url(self, url: str, is_complex: bool) -> str:
            )
        return url

    # ================================
    # 📥 بارگذاری لیست URLها
    # ================================
    def _load_entries(self, file_path: str, is_complex: bool) -> List[Tuple[str, str]]:
        """
        فایل ورودی را می‌خواند و لیست URLها را استخراج می‌کند.
        هر خط باید به شکل `filename|url` باشد.
        """
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line:
                        # اگر فرمت خط صحیح نباشد، آن را رد می‌کنیم
                        continue
                    filename, url = line.strip().split("|", 1)
                    processed_url = self._process_url(url.strip(), is_complex)
                    entries.append((filename.strip(), processed_url))
        except FileNotFoundError:
            logging.error(f"⚠️ فایل {file_path} یافت نشد! بررسی کنید که وجود دارد.")
        return entries

    # ================================
    # 🔄 جایگزینی URL در قالب
    # ================================
    def _replace_proxy_url(self, template: str, new_url: str) -> str:
        """
        جایگزینی URL در بخش `proxy-providers` فایل قالب.
        """
        pattern = re.compile(
            r'(proxy-providers:\s*\n\s+proxy:\s*\n\s+type:\s*http\s*\n\s+url:\s*>?-?\s*\n\s+)([^\n]+)',
            re.DOTALL
        )
        return pattern.sub(rf'\g<1>{new_url}', template)

    # ================================
    # 📂 جایگزینی مسیر فایل (Path)
    # ================================
    def _replace_proxy_path(self, template: str, new_path: str) -> str:
        """
        جایگزینی `path` در بخش proxy-providers.
        این بخش تضمین می‌کند فایل خروجی نهایی به مسیر جدید اشاره کند.
        """
        pattern = re.compile(
            r"(\n\s+include-all:\s*(?:true|false)\s*\n\s+path:\s*)([^\n]+)",
            re.IGNORECASE
        )
        return pattern.sub(rf'\g<1>{new_path}', template, count=1)

    # ================================
    # 📝 تولید فایل README
    # ================================
    def _generate_readme(self, entries: List[Tuple[str, str]]) -> None:
        """
        تولید فایل README شامل لینک مستقیم به فایل‌های کانفیگ.
        """
        md_content = [
            "# 📂 لیست کانفیگ‌های کلش متا",
            "### با قوانین مخصوص ایران\n",
            "**فایل‌های پیکربندی آماده استفاده:**\n"
        ]

        # برای تنوع در آیکون‌ها، هر فایل یک ایموجی متفاوت می‌گیرد
        emojis = ["🌐", "🚀", "🔒", "⚡", "🛡️"]
        for idx, (filename, _) in enumerate(entries):
            emoji = emojis[idx % len(emojis)]
            file_url = f"{self.base_url}{urllib.parse.quote(filename)}"
            md_content.append(f"- [{emoji} {filename}]({file_url})")

        # افزودن بخش‌های آموزشی
        md_content.extend([
            "\n## 📖 راهنمای استفاده",
            "1. روی لینک مورد نظر **کلیک راست** کنید",
            "2. گزینه **«کپی لینک»** را انتخاب کنید",
            "3. لینک را در کلش متا **وارد کنید**\n",

            "## ⭐ ویژگی‌ها",
            "- 🚀 بهینه‌شده برای ایران",
            "- 🔄 فعال و غیر فعال کردن راحت قوانین",
            "- 📆 آپدیت روزانه\n",

            "## 📥 دریافت کلاینت",
            "### ویندوز",  
            "[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)",

            "### اندروید",
            "[ClashMeta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid/releases)"
        ])

        with open(self.readme_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_content))

    # ================================
    # ⚙️ تولید فایل‌های نهایی
    # ================================
    def generate_configs(self):
        """
        مرحله اصلی پردازش:
        1. بارگذاری لیست‌ها
        2. ادغام URLهای ساده و پیچیده
        3. اعمال تغییرات روی قالب
        4. ذخیره فایل‌های خروجی
        5. تولید README
        """
        # مرحله ۱: بارگذاری لیست‌ها
        simple_entries = self._load_entries(self.simple_list, False)
        complex_entries = self._load_entries(self.complex_list, True)

        # مرحله ۲: ادغام لیست‌ها (اولویت با لیست ساده است)
        merged = {}
        for name, url in simple_entries + complex_entries:
            if name not in merged:
                merged[name] = url

        # مرحله ۳: خواندن قالب اصلی
        with open(self.template_path, "r", encoding="utf-8") as f:
            original_template = f.read()

        # مرحله ۴: اطمینان از وجود پوشه خروجی
        os.makedirs(self.output_dir, exist_ok=True)

        # مرحله ۵: پردازش هر فایل به صورت جداگانه
        merged_items = list(merged.items())

        for idx, (filename, url) in enumerate(merged_items):
            # جایگزینی URL
            modified = self._replace_proxy_url(original_template, url)

            # جایگزینی مسیر فایل
            new_path = f"./MihomoSaz{idx + 1}.yaml"
            modified = self._replace_proxy_path(modified, new_path)

            # مسیر خروجی
            output_path = os.path.join(self.output_dir, filename)

            # اگر مسیر دارای پوشه‌های میانی باشد، آن‌ها را ایجاد می‌کنیم
            dir_path = os.path.dirname(output_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            # ذخیره فایل خروجی
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(modified)

        # مرحله ۶: تولید README
        self._generate_readme(merged_items)
        logging.info("✅ همه فایل‌ها با موفقیت ساخته شدند!")

# ================================
# 🚀 اجرای برنامه اصلی
# ================================
if __name__ == "__main__":
    try:
        processor = ConfigProcessor()
        processor.generate_configs()
        logging.info("🎉 پردازش با موفقیت به پایان رسید!")
    except Exception as e:
        logging.critical(f"❌ خطا در اجرای برنامه: {e}", exc_info=True)
