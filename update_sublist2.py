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
                "%2Funiversal%2Furltest.ini&emoji=false"
                "&append_type=true&append_info=true&scv=true"
                "&udp=true&list=true&sort=false&fdn=true"
                "&insert=false"
            )
        return url

    def _load_entries(self, file_path: str, is_complex: bool) -> List[Tuple[str, str]]:
        """بارگذاری لیست URLها"""
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|" not in line:
                        continue
                    filename, url = line.strip().split("|", 1)
                    processed_url = self._process_url(url.strip(), is_complex)
                    entries.append((filename.strip(), processed_url))
        except FileNotFoundError:
            logging.error(f"فایل {file_path} یافت نشد!")
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
        """تولید README با لینک مستقیم (Simple و Complex جدا)"""
        md_content = [
            "# 📂 لیست کانفیگ‌های کلش متا",
            "### با قوانین مخصوص ایران\n",
            "**فایل‌های پیکربندی آماده استفاده:**\n"
        ]
        
        emojis = ["🌐", "🚀", "🔒", "⚡", "🛡️"]

        # Simple section
        md_content.append("## 🔹 Simple Links\n")
        for idx, (filename, _) in enumerate(simple_entries):
            emoji = emojis[idx % len(emojis)]
            file_url = f"{self.base_url}Simple/{urllib.parse.quote(filename)}"
            md_content.append(f"- {emoji} [{filename}]({file_url})")
        
        # Complex section
        md_content.append("\n## 🔸 Complex Links\n")
        for idx, (filename, _) in enumerate(complex_entries):
            emoji = emojis[idx % len(emojis)]
            file_url = f"{self.base_url}Complex/{urllib.parse.quote(filename)}"
            md_content.append(f"- {emoji} [{filename}]({file_url})")

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

    def _generate_configs_for_list(self, entries: List[Tuple[str, str]], subdir: str) -> None:
        """ساخت فایل‌های YAML برای یک لیست خاص"""
        if not entries:
            return

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

    def generate_configs(self):
        """تولید فایل‌های پیکربندی برای Simple و Complex"""
        simple_entries = self._load_entries(self.simple_list, False)
        complex_entries = self._load_entries(self.complex_list, True)

        # تولید فایل‌ها
        self._generate_configs_for_list(simple_entries, "Simple")
        self._generate_configs_for_list(complex_entries, "Complex")

        # تولید README
        self._generate_readme(simple_entries, complex_entries)
        logging.info("فایل‌ها با موفقیت ساخته شدند!")


if __name__ == "__main__":
    try:
        processor = ConfigProcessor()
        processor.generate_configs()
        logging.info("✅ پردازش با موفقیت انجام شد!")
    except Exception as e:
        logging.critical(f"❌ خطا: {e}", exc_info=True)
