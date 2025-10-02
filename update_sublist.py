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
            "## 📥 دریافت کلاینت‌های Clash.Meta / Mihomo",
            "### ویندوز",
            "- [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases) : Modern Tauri-based cross-platform GUI, lightweight, supports advanced routing and DNS over HTTPS, occasional minor UI bugs. Pros: fast, simple setup, stable updates. Cons: fewer themes, small learning curve for advanced routing. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Verge](https://github.com/clash-verge/clash-verge/releases) : Stable cross-platform client, simple interface, supports basic proxy management. Pros: stable, lightweight. Cons: fewer advanced features than Verge Rev. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Clash Nyanpasu](https://github.com/LibNyanpasu/clash-nyanpasu/releases) : Minimalist design, lightweight, easy to use, focused on essential features. Pros: fast, low resource usage. Cons: lacks advanced routing and load balancing. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5",
            "- [Clash N](https://github.com/2dust/clashN/releases) : Clean GUI, user-friendly, supports basic rules and subscription updates. Pros: simple, stable. Cons: limited customization, fewer advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases) : Minimalistic client for essential routing, low resource usage. Pros: fast, portable. Cons: no advanced GUI, limited proxy management. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5",
            "- [ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases) : macOS style interface on Windows, rich feature set including rule-based routing, DNS over HTTPS. Pros: advanced features, cross-platform compatibility. Cons: occasional UI glitches, slightly higher resource usage. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash for Windows](https://en.clashforwindows.org/) : Full-featured GUI, popular among Windows users, supports subscriptions, rules, and multiple proxies. Pros: rich GUI, stable, frequent updates. Cons: slightly heavier, may require manual updates. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop) : Optimized for speed, lightweight, supports load balancing and DNS features. Pros: fast, optimized, lightweight. Cons: less documentation, fewer GUI customization options. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess",
            "- [FlClash](https://github.com/chen08209/FlClash/releases) : Multi-platform, open-source, ad-free, supports advanced rules and proxies. Pros: simple, ad-free, stable. Cons: limited GUI customization. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClashX](https://github.com/pluralplay/FlClashX) : Enhanced FlClash with extra features, better stability, added proxy management tools. Pros: more features, active updates. Cons: slightly higher resource usage. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Mihomo Party](https://github.com/mihomo-party-org/clash-party) : Community-driven, supports multiple protocols and subscriptions, rich features. Pros: frequent updates, community support. Cons: complex for beginners. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Pandora Box](https://github.com/LibNyanpasu/pandora-box) : Advanced features, supports multiple proxies, rule management, DNS over HTTPS. Pros: robust features. Cons: heavier than most clients. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [AnyPortal](https://github.com/AnyPortal) : Versatile client, supports various protocols, active development. Pros: flexible, protocol-rich. Cons: less user-friendly. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop) : User-friendly, minimalistic, supports basic proxy management and subscriptions. Pros: simple, portable. Cons: lacks advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "### MacOS",
            "- [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases) : Modern Tauri-based cross-platform GUI, lightweight, advanced routing and DNS support. Pros: stable, fast. Cons: minor UI bugs. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Verge](https://github.com/clash-verge/clash-verge/releases) : Stable, simple interface, supports basic proxies. Pros: lightweight, stable. Cons: lacks advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases) : macOS-focused, advanced routing, rule-based proxy management. Pros: full-featured, stable. Cons: higher resource usage. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases) : Minimalistic, lightweight, essential features. Pros: fast, portable. Cons: lacks GUI, limited advanced options. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5",
            "- [HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop) : Optimized, fast, supports DNS and load balancing. Pros: lightweight, fast. Cons: less documentation. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess",
            "- [FlClash](https://github.com/chen08209/FlClash/releases) : Open-source, ad-free, multi-platform, rule support. Pros: simple, ad-free. Cons: limited GUI customization. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClashX](https://github.com/pluralplay/FlClashX) : Enhanced FlClash with extra features and stability. Pros: more features, active updates. Cons: higher resource usage. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Mihomo Party](https://github.com/mihomo-party-org/clash-party) : Community-driven, protocol-rich, subscription support. Pros: active updates, community support. Cons: complex for beginners. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Pandora Box](https://github.com/LibNyanpasu/pandora-box) : Advanced proxy and DNS management. Pros: feature-rich. Cons: heavier, complex. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [AnyPortal](https://github.com/AnyPortal) : Flexible, multi-protocol support. Pros: versatile. Cons: less beginner-friendly. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop) : User-friendly, lightweight. Pros: simple, portable. Cons: lacks advanced routing. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "### لینوکس",
            "- [Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases) : Lightweight, cross-platform Tauri GUI. Pros: stable, fast. Cons: minor UI bugs. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Verge](https://github.com/clash-verge/clash-verge/releases) : Stable, minimal interface. Pros: fast, simple. Cons: fewer advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases) : Minimal, essential features. Pros: lightweight, fast. Cons: limited advanced options. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5",
            "- [ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases) : Feature-rich GUI. Pros: advanced features. Cons: higher resources. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop) : Optimized for speed. Pros: lightweight. Cons: less documentation. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess",
            "- [FlClash](https://github.com/chen08209/FlClash/releases) : Open-source, ad-free, multi-platform. Pros: simple, stable. Cons: limited GUI customization. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClashX](https://github.com/pluralplay/FlClashX) : Enhanced FlClash. Pros: extra features. Cons: higher resource usage. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Mihomo Party](https://github.com/mihomo-party-org/clash-party) : Protocol-rich, subscription support. Pros: active community. Cons: complex for beginners. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Mihoro](https://github.com/spencerwooo/mihoro) : Lightweight, fast. Pros: minimal, efficient. Cons: lacks GUI features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Pandora Box](https://github.com/LibNyanpasu/pandora-box) : Feature-rich. Pros: advanced. Cons: heavy. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [AnyPortal](https://github.com/AnyPortal/AnyPortal) : Versatile. Pros: multi-protocol. Cons: less user-friendly. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop) : Lightweight, user-friendly. Pros: simple. Cons: lacks advanced routing. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks"
            "### اندروید",
            "- [ClashMeta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid/releases) : Official Android client, rule-based routing, supports subscriptions, DNS over HTTPS. Pros: stable, regular updates. Cons: UI less customizable. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClash](https://github.com/chen08209/FlClash/releases) : Multi-platform, ad-free, optimized for Android. Pros: simple, lightweight, open-source. Cons: limited GUI customization. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClashX](https://github.com/pluralplay/FlClashX) : Enhanced FlClash for Android, more features and stability. Pros: feature-rich, actively updated. Cons: slightly higher resource usage. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Karing](https://github.com/KaringX/karing/releases) : User-friendly, minimalistic, supports rule-based routing. Pros: easy to use, lightweight. Cons: fewer advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Surfboard](https://github.com/MetaCubeX/Surfboard/releases) : Lightweight, stable, supports multiple proxies. Pros: fast, simple. Cons: limited advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [ClashMi](https://github.com/KaringX/clashmi) : Minimalistic Android client, supports subscriptions. Pros: simple, fast. Cons: lacks advanced routing options. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Clash Mi Android Fork](https://github.com/KaringX/clashmi-android) : Android-specific enhancements, updated forks. Pros: additional features. Cons: may be less stable. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Mihomo Party](https://github.com/mihomo-party-org/clash-party) : Community-driven, supports multiple protocols. Pros: active updates. Cons: complex for beginners. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [NekoBox](https://github.com/MatsuriDayo/NekoBoxForAndroid/releases) : Feature-rich, subscription management, advanced rules. Pros: versatile. Cons: slightly heavier. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Hiddify](https://github.com/hiddify/hiddify-app/releases) : Optimized Android client, supports load balancing. Pros: lightweight, fast. Cons: less documentation. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess",
            "- [AnyPortal](https://github.com/AnyPortal/AnyPortal) : Multi-protocol Android client. Pros: flexible. Cons: less beginner-friendly. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Pandora Box](https://github.com/LibNyanpasu/pandora-box) : Advanced features and rules on Android. Pros: rich features. Cons: heavier. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS"
            "### iOS",
            "- [FlClash (iOS)](https://github.com/chen08209/FlClash/releases) : Multi-platform, ad-free, supports rules and proxies. Pros: simple, stable. Cons: limited GUI customization. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [FlClashX](https://github.com/pluralplay/FlClashX) : Enhanced FlClash for iOS, more features and stability. Pros: actively updated, feature-rich. Cons: higher resource usage. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Stash](https://apps.apple.com/app/stash/id1596063349) : Professional iOS client, rule-based routing, subscription support. Pros: stable, advanced features. Cons: paid, complex for beginners. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash iOS](https://bestclash.net/en/products/ios) : User-friendly iOS client, GUI-based configuration. Pros: easy to use. Cons: fewer advanced features. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Clash Mi (TestFlight)](https://testflight.apple.com/join/bjHXktB3) : Beta version, experimental features. Pros: cutting-edge, early access. Cons: may be unstable. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [ClashMi](https://apps.apple.com/us/app/clash-mi/id6744321968) : Minimalistic iOS client, simple proxy management. Pros: lightweight, simple. Cons: lacks advanced routing. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks",
            "- [Shadowrocket](https://apps.apple.com/us/app/shadowrocket/id932747118) : Advanced client, supports multiple protocols. Pros: stable, feature-rich. Cons: paid. Supported cores: Clash.Meta, Clash, V2Ray. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Quantumult X](https://apps.apple.com/us/app/quantumult-x/id1443988620) : Feature-rich, rule-based proxy client. Pros: advanced rules, automation. Cons: paid, complex for beginners. Supported cores: Clash.Meta, Clash, V2Ray. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Surge](https://apps.apple.com/us/app/surge/id1228589927) : Professional proxy client, automation features. Pros: robust, advanced. Cons: paid, heavier learning curve. Supported cores: Clash.Meta, Clash, V2Ray. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [AnyPortal](https://github.com/AnyPortal/AnyPortal) : iOS multi-protocol client. Pros: versatile. Cons: less beginner-friendly. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Pandora Box](https://github.com/LibNyanpasu/pandora-box) : Advanced iOS client. Pros: rich features. Cons: heavier. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS"
            "### سایر پلتفرم‌ها",
            "- [Clash Web Dashboard](https://github.com/Dreamacro/clash-dashboard) : Web-based GUI for Clash running on any platform with a web server. Pros: cross-platform, no installation needed. Cons: requires existing Clash core. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash on OpenWRT](https://github.com/vernesong/OpenClash) : Router-based Clash client for OpenWRT firmware. Pros: runs on routers, automatic routing, ad blocking. Cons: setup more technical, resource-limited. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash on Raspberry Pi](https://github.com/Dreamacro/clash) : Lightweight Clash core running on ARM Linux. Pros: low power, portable. Cons: CLI-based, no GUI. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash on ASUSWRT/Merlin](https://github.com/MetaCubeX/Clash-for-Routers) : Router client for ASUS firmware. Pros: runs on home routers, stable. Cons: limited UI, technical setup. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash CLI (Linux/BSD)](https://github.com/Dreamacro/clash) : Command-line interface for advanced users. Pros: lightweight, scriptable. Cons: no GUI, requires configuration files. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Clash on Tomato / Mikrotik](https://github.com/MetaCubeX/Clash-for-Routers) : Embedded router solution. Pros: centralized routing for home network. Cons: firmware-specific, advanced setup. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS"
            "- [OpenWrt‑nikki](https://github.com/nikkinikki-org/OpenWrt-nikki) : OpenWRT router client for Clash.Meta, supports rule-based routing. Pros: stable on routers, centralized proxy. Cons: requires router with OpenWRT. Supported cores: Clash.Meta. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
            "- [Mihomo Transparent Proxy (Docker)](https://github.com/scenery/mihomo-tproxy-docker) : Dockerized transparent proxy for any platform, easy deployment. Pros: portable, cross-platform. Cons: requires Docker knowledge. Supported cores: Clash.Meta, Clash. Supported agents: HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS",
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
