import os
import re
import urllib.parse
import logging
from typing import List, Tuple

# تنظیمات لاگ
logging.basicConfig(
    filename="update.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

class ConfigProcessor:
    def __init__(self):
        self.template_path = "mihomo_template.yml"
        self.output_dir = "Sublist"
        self.readme_path = "README.md"
        self.base_url = "https://raw.githubusercontent.com/asgharkapk/Free-Clash-Meta/main/Sublist/"
        self.simple_list = "Simple_URL_List.txt"
        self.complex_list = "Complex_URL_list.txt"

    def _process_url(self, url: str, is_complex: bool) -> str:
        """پردازش URL بر اساس نوع لیست"""
        if is_complex:
            encoded = urllib.parse.quote(url, safe=':/?&=')
            return (
                "https://url.v1.mk/sub?&url="
                f"{encoded}&target=clash&config="
                "https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2FSleepyHeeead"
                "%2Fsubconverter-config%40master%2Fremote-config"
                "%2Funiversal%2Furltest.ini&add_emoji=true"
                "&append_type=true&append_info=true&scv=true"
                "&udp=true&list=true&sort=false&fdn=true"
                "&insert=false"
            )
        return url

    def _load_entries(self, file_path: str, is_complex: bool) -> List[Tuple[str, str]]:
        """بارگذاری لیست URLها"""
        entries = []
        try:
            logging.info(f"🔍 شروع خواندن لیست: {file_path} (complex={is_complex})")
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line:
                        logging.warning(f"⏭️ خط بی‌اعتبار در {file_path}: {line.strip()}")
                        continue
                    filename, url = line.strip().split("|", 1)
                    processed_url = self._process_url(url.strip(), is_complex)
                    entries.append((filename.strip(), processed_url))
                    logging.debug(f"📌 ورودی بارگذاری شد: {filename.strip()} -> {processed_url}")
            logging.info(f"✅ تعداد {len(entries)} ورودی از {file_path} خوانده شد")
        except FileNotFoundError:
            logging.error(f"❌ فایل {file_path} یافت نشد!")
        return entries

    def _replace_proxy_url(self, template: str, new_url: str) -> str:
        """جایگزینی URL در بخش proxy-providers"""
        pattern = re.compile(
            r"(url:\s*(?:>-\s*|\|-\s*)?\n\s*)([^\n]+)",
            re.IGNORECASE
        )
        return pattern.sub(rf"\1{new_url}", template, count=1)
    
    def _replace_proxy_path(self, template: str, new_path: str) -> str:
        """جایگزینی path در بخش proxy-providers با دقت"""
        pattern = re.compile(
            r"(include-all:\s*(?:true|false)\s*\n\s*path:\s*)([^\n]+)",
            re.IGNORECASE
        )
        return pattern.sub(rf"\1{new_path}", template, count=1)

    def _generate_readme(self, simple_entries: List[Tuple[str, str]], complex_entries: List[Tuple[str, str]]) -> None:
        """تولید README به صورت جدول (Simple و Complex کنار هم با نام یکسان)"""
        logging.info("📝 شروع تولید README.md ...")
        md_content = [
            "# 📂 لیست کانفیگ‌های کلش متا",
            "### با قوانین مخصوص ایران\n",
            "**فایل‌های پیکربندی آماده استفاده:**\n",
            ""
        ]
    
        emojis = ["🌐", "🚀", "🔒", "⚡", "🛡️"]
    
        # تبدیل لیست‌ها به دیکشنری (کلید: filename)
        simple_dict = {fn: fn for fn, _ in simple_entries}
        complex_dict = {fn: fn for fn, _ in complex_entries}
    
        # تمام نام‌ها
        all_filenames = sorted(set(simple_dict.keys()) | set(complex_dict.keys()))
    
        # ۱. فایل‌هایی که در هر دو دسته هستند (Simple ↔ Complex)
        paired_files = [fn for fn in all_filenames if fn in simple_dict and fn in complex_dict]
    
        if paired_files:
            md_content.append("## 🔗 لینک‌ها (Simple ↔ Complex)\n")
            md_content.append("| Simple | Complex |")
            md_content.append("|--------|---------|")
    
            for idx, filename in enumerate(paired_files):
                emoji = emojis[idx % len(emojis)]
                s_file_url = f"{self.base_url}Simple/{urllib.parse.quote(filename)}"
                c_file_url = f"{self.base_url}Complex/{urllib.parse.quote(filename)}"
                md_content.append(f"| {emoji} [{filename}]({s_file_url}) | {emoji} [{filename}]({c_file_url}) |")
    
        # ۲. فایل‌های یکتا در Simple
        unique_simple = [fn for fn in simple_dict.keys() if fn not in complex_dict]
        if unique_simple:
            md_content.append("\n## 🔹 فقط Simple\n")
            for idx, filename in enumerate(unique_simple):
                emoji = emojis[idx % len(emojis)]
                s_file_url = f"{self.base_url}Simple/{urllib.parse.quote(filename)}"
                md_content.append(f"- {emoji} [{filename}]({s_file_url})")
    
        # ۳. فایل‌های یکتا در Complex
        unique_complex = [fn for fn in complex_dict.keys() if fn not in simple_dict]
        if unique_complex:
            md_content.append("\n## 🔹 فقط Complex\n")
            for idx, filename in enumerate(unique_complex):
                emoji = emojis[idx % len(emojis)]
                c_file_url = f"{self.base_url}Complex/{urllib.parse.quote(filename)}"
                md_content.append(f"- {emoji} [{filename}]({c_file_url})")
    
        # Footer
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
        logging.info(f"✅ README.md ساخته شد ({len(simple_entries)} Simple, {len(complex_entries)} Complex)")
            
    def _generate_configs_for_list(self, entries: List[Tuple[str, str]], subdir: str) -> None:
        """ساخت فایل‌های YAML برای یک لیست خاص"""
        if not entries:
            logging.warning(f"⚠️ لیست {subdir} خالی است، هیچ فایلی ساخته نشد")
            return
        logging.info(f"📂 شروع تولید فایل‌ها برای {subdir} (تعداد: {len(entries)})")
        with open(self.template_path, "r", encoding="utf-8") as f:
            original_template = f.read()

        output_subdir = os.path.join(self.output_dir, subdir)
        os.makedirs(output_subdir, exist_ok=True)

        for idx, (filename, url) in enumerate(entries):
            modified = self._replace_proxy_url(original_template, url)
            new_path = f"./FCM_{subdir}_{idx + 1}.yaml"
            modified = self._replace_proxy_path(modified, new_path)

            output_path = os.path.join(output_subdir, filename)
            dir_path = os.path.dirname(output_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(modified)
            logging.info(f"📄 فایل ساخته شد: {output_path} (URL جایگزین شد)")
        logging.info(f"✅ همه فایل‌های {subdir} ساخته شدند ({len(entries)} فایل)")

    def _save_complex_urls(self, complex_entries: List[Tuple[str, str]]) -> None:
        """ذخیره لیست URLهای پردازش‌شده Complex در یک فایل جداگانه"""
        if not complex_entries:
            logging.warning("⚠️ لیست Complex خالی است، خروجی URL ساخته نشد")
            return

        output_file = "Complex_Processed_URLs.txt"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for filename, url in complex_entries:
                    f.write(f"{url},{filename}\n")
            logging.info(f"✅ فایل {output_file} ساخته شد ({len(complex_entries)} URL)")
        except Exception as e:
            logging.error(f"❌ خطا در نوشتن فایل Complex URLs: {e}")
    
    def generate_configs(self):
        """تولید فایل‌های پیکربندی برای Simple و Complex"""
        logging.info("🚀 شروع پردازش کل پیکربندی‌ها")
        simple_entries = self._load_entries(self.simple_list, False)
        complex_entries = self._load_entries(self.complex_list, True)

        # تولید فایل‌ها
        self._generate_configs_for_list(simple_entries, "Simple")
        self._generate_configs_for_list(complex_entries, "Complex")

        # ذخیره لیست پردازش‌شده Complex
        self._save_complex_urls(complex_entries)

        # تولید README
        self._generate_readme(simple_entries, complex_entries)
        logging.info("🎉 پردازش کامل شد: فایل‌ها و README ساخته شدند")

if __name__ == "__main__":
    try:
        processor = ConfigProcessor()
        processor.generate_configs()
        logging.info("✅ پردازش با موفقیت انجام شد!")
    except Exception as e:
        logging.critical(f"❌ خطا: {e}", exc_info=True)
