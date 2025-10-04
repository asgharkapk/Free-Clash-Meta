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
                for line_number, line in enumerate(f, start=1):
                    stripped = line.strip()
                    if "|" not in stripped or not stripped:
                        logging.warning(
                            f"⏭️ خط بی‌اعتبار در {file_path} (شماره خط {line_number}): {repr(stripped)}"
                        )
                        continue
                    filename, url = stripped.split("|", 1)
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
    
        emojis = [
            "🌐", "🚀", "🔒", "⚡", "🛡️", "🔥", "💎", "🎯", "🌀", "🌟",
            "⚙️", "📡", "📌", "🧩", "🎵", "🌈", "💡", "🏹", "🛠️", "🧭",
            "🧨", "💫", "🕹️", "📌", "🎁", "⚡️", "🎯", "🏆", "🥇", "🌊"
        ]
    
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
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)|Modern Tauri-based cross-platform GUI, lightweight, supports advanced routing and DNS over HTTPS, occasional minor UI bugs.|Fast, simple setup, stable updates.|Fewer themes, small learning curve for advanced routing.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash Verge](https://github.com/clash-verge/clash-verge/releases)|Stable cross-platform client, simple interface, supports basic proxy management.|Stable, lightweight.|Fewer advanced features than Verge Rev.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Clash Nyanpasu](https://github.com/LibNyanpasu/clash-nyanpasu/releases)|Minimalist design, lightweight, easy to use, focused on essential features.|Fast, low resource usage.|Lacks advanced routing and load balancing.|Clash.Meta, Clash, Mihomo, Mihomo Alpha|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Trojan, Snell, Hysteria, Tuic|",
            "|[Clash N](https://github.com/2dust/clashN/releases)|Clean GUI, user-friendly, supports basic rules and subscription updates.|Simple, stable.|Limited customization, fewer advanced features.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases)|Minimalistic client for essential routing, low resource usage.|Fast, portable.|No advanced GUI, limited proxy management.|Clash.Meta|HTTP, HTTPS, SOCKS5|",
            "|[ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases)|macOS style interface on Windows, rich feature set including rule-based routing, DNS over HTTPS.|Advanced features, cross-platform compatibility.|Occasional UI glitches, slightly higher resource usage.|Clash.Meta|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash for Windows](https://en.clashforwindows.org/)|Full-featured GUI, popular among Windows users, supports subscriptions, rules, and multiple proxies.|Rich GUI, stable, frequent updates.|Slightly heavier, may require manual updates.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Trojan, Snell, Wireguard|",
            "|[HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop)|Optimized for speed, lightweight, supports load balancing and DNS features.|Fast, optimized, lightweight.|Less documentation, fewer GUI customization options.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Hysteria, Tuic|",
            "|[FlClash](https://github.com/chen08209/FlClash/releases)|Multi-platform, open-source, ad-free, supports advanced rules and proxies.|Simple, ad-free, stable.|Limited GUI customization.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClashX](https://github.com/pluralplay/FlClashX)|Enhanced FlClash with extra features, better stability, added proxy management tools.|More features, active updates.|Slightly higher resource usage.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Mihomo Party](https://github.com/mihomo-party-org/clash-party)|Community-driven, supports multiple protocols and subscriptions, rich features.|Frequent updates, community support.|Complex for beginners.|Mihomo|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Hysteria, Tuic|",
            "|[Pandora Box](https://github.com/LibNyanpasu/pandora-box)|Advanced features, supports multiple proxies, rule management, DNS over HTTPS.|Robust features.|Heavier than most clients.|Clash.Meta|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Trojan, Snell, Wireguard|",
            "|[AnyPortal](https://github.com/AnyPortal)|Versatile client, supports various protocols, active development.|Flexible, protocol-rich.|Less user-friendly.|Clash.Meta|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS, Trojan, Snell, Wireguard|",
            "|[Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop)|User-friendly, minimalistic, supports basic proxy management and subscriptions.|Simple, portable.|Lacks advanced features.|Clash.Meta, Clash|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "### MacOS",
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)|Modern Tauri-based cross-platform GUI, lightweight, advanced routing and DNS support.|stable, fast.|minor UI bugs.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash Verge](https://github.com/clash-verge/clash-verge/releases)|Stable, simple interface, supports basic proxies.|lightweight, stable.|lacks advanced features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases)|macOS-focused, advanced routing, rule-based proxy management.|full-featured, stable.|higher resource usage.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases)|Minimalistic, lightweight, essential features.|fast, portable.|lacks GUI, limited advanced options.|Clash.Meta.|HTTP, HTTPS, SOCKS5|",
            "|[HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop)|Optimized, fast, supports DNS and load balancing.|lightweight, fast.|less documentation.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess|",
            "|[FlClash](https://github.com/chen08209/FlClash/releases)|Open-source, ad-free, multi-platform, rule support.|simple, ad-free.|limited GUI customization.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClashX](https://github.com/pluralplay/FlClashX)|Enhanced FlClash with extra features and stability.|more features, active updates.|higher resource usage.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Mihomo Party](https://github.com/mihomo-party-org/clash-party)|Community-driven, protocol-rich, subscription support.|active updates, community support.|complex for beginners.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Pandora Box](https://github.com/LibNyanpasu/pandora-box)|Advanced proxy and DNS management.|feature-rich.|heavier, complex.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[AnyPortal](https://github.com/AnyPortal)|Flexible, multi-protocol support.|versatile.|less beginner-friendly.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop)|User-friendly, lightweight.|simple, portable.|lacks advanced routing.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "### لینوکس",
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[Clash Verge Rev](https://github.com/clash-verge-rev/clash-verge-rev/releases)|Lightweight, cross-platform Tauri GUI.|stable, fast.|minor UI bugs.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash Verge](https://github.com/clash-verge/clash-verge/releases)|Stable, minimal interface.|fast, simple.|fewer advanced features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Clash.Mini](https://github.com/MetaCubeX/Clash.Mini/releases)|Minimal, essential features.|lightweight, fast.|limited advanced options.|Clash.Meta.|HTTP, HTTPS, SOCKS5|",
            "|[ClashX.Meta](https://github.com/MetaCubeX/ClashX.Meta/releases)|Feature-rich GUI.|advanced features.|higher resources.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[HiddifyClashDesktop](https://github.com/hiddify/HiddifyClashDesktop)|Optimized for speed.|lightweight.|less documentation.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess|",
            "|[FlClash](https://github.com/chen08209/FlClash/releases)|Open-source, ad-free, multi-platform.|simple, stable.|limited GUI customization.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClashX](https://github.com/pluralplay/FlClashX)|Enhanced FlClash.|extra features.|higher resource usage.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Mihomo Party](https://github.com/mihomo-party-org/clash-party)|Protocol-rich, subscription support.|active community.|complex for beginners.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Mihoro](https://github.com/spencerwooo/mihoro)|Lightweight, fast.|minimal, efficient.|lacks GUI features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Pandora Box](https://github.com/LibNyanpasu/pandora-box)|Feature-rich.|advanced.|heavy.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[AnyPortal](https://github.com/AnyPortal/AnyPortal)|Versatile.|multi-protocol.|less user-friendly.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash Mi Desktop](https://github.com/KaringX/clashmi-desktop)|Lightweight, user-friendly.|simple.|lacks advanced routing.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "### اندروید",
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[ClashMeta for Android](https://github.com/MetaCubeX/ClashMetaForAndroid/releases)|Official Android client, rule-based routing, supports subscriptions, DNS over HTTPS.|stable, regular updates.|UI less customizable.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClash](https://github.com/chen08209/FlClash/releases)|Multi-platform, ad-free, optimized for Android.|simple, lightweight, open-source.|limited GUI customization.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClashX](https://github.com/pluralplay/FlClashX)|Enhanced FlClash for Android, more features and stability.|feature-rich, actively updated.|slightly higher resource usage.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Karing](https://github.com/KaringX/karing/releases)|User-friendly, minimalistic, supports rule-based routing.|easy to use, lightweight.|fewer advanced features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Surfboard](https://github.com/MetaCubeX/Surfboard/releases)|Lightweight, stable, supports multiple proxies.|fast, simple.|limited advanced features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[ClashMi](https://github.com/KaringX/clashmi)|Minimalistic Android client, supports subscriptions.|simple, fast.|lacks advanced routing options.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Clash Mi Android Fork](https://github.com/KaringX/clashmi-android)|Android-specific enhancements, updated forks.|additional features.|may be less stable.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Mihomo Party](https://github.com/mihomo-party-org/clash-party)|Community-driven, supports multiple protocols.|active updates.|complex for beginners.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[NekoBox](https://github.com/MatsuriDayo/NekoBoxForAndroid/releases)|Feature-rich, subscription management, advanced rules.|versatile.|slightly heavier.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Hiddify](https://github.com/hiddify/hiddify-app/releases)|Optimized Android client, supports load balancing.|lightweight, fast.|less documentation.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess|",
            "|[AnyPortal](https://github.com/AnyPortal/AnyPortal)|Multi-protocol Android client.|flexible.|less beginner-friendly.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Pandora Box](https://github.com/LibNyanpasu/pandora-box)|Advanced features and rules on Android.|rich features.|heavier.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "### iOS",
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[FlClash (iOS)](https://github.com/chen08209/FlClash/releases)|Multi-platform, ad-free, supports rules and proxies.|simple, stable.|limited GUI customization.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[FlClashX](https://github.com/pluralplay/FlClashX)|Enhanced FlClash for iOS, more features and stability.|actively updated, feature-rich.|higher resource usage.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Stash](https://apps.apple.com/app/stash/id1596063349)|Professional iOS client, rule-based routing, subscription support.|stable, advanced features.|paid, complex for beginners.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash iOS](https://bestclash.net/en/products/ios)|User-friendly iOS client, GUI-based configuration.|easy to use.|fewer advanced features.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Clash Mi (TestFlight)](https://testflight.apple.com/join/bjHXktB3)|Beta version, experimental features.|cutting-edge, early access.|may be unstable.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[ClashMi](https://apps.apple.com/us/app/clash-mi/id6744321968)|Minimalistic iOS client, simple proxy management.|lightweight, simple.|lacks advanced routing.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks|",
            "|[Shadowrocket](https://apps.apple.com/us/app/shadowrocket/id932747118)|Advanced client, supports multiple protocols.|stable, feature-rich.|paid.|Clash.Meta, Clash, V2Ray.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Quantumult X](https://apps.apple.com/us/app/quantumult-x/id1443988620)|Feature-rich, rule-based proxy client.|advanced rules, automation.|paid, complex for beginners.|Clash.Meta, Clash, V2Ray.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Surge](https://apps.apple.com/us/app/surge/id1228589927)|Professional proxy client, automation features.|robust, advanced.|paid, heavier learning curve.|Clash.Meta, Clash, V2Ray.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[AnyPortal](https://github.com/AnyPortal/AnyPortal)|iOS multi-protocol client.|versatile.|less beginner-friendly.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Pandora Box](https://github.com/LibNyanpasu/pandora-box)|Advanced iOS client.|rich features.|heavier.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "### سایر پلتفرم‌ها",
            "|Client|Description|Pros|Cons|Supported cores|Supported agents|",
            "|-|-|-|-|-|-|",
            "|[Clash Web Dashboard](https://github.com/Dreamacro/clash-dashboard)|Web-based GUI for Clash running on any platform with a web server.|cross-platform, no installation needed.|requires existing Clash core.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash on OpenWRT](https://github.com/vernesong/OpenClash)|Router-based Clash client for OpenWRT firmware.|runs on routers, automatic routing, ad blocking.|setup more technical, resource-limited.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash on Raspberry Pi](https://github.com/Dreamacro/clash)|Lightweight Clash core running on ARM Linux.|low power, portable.|CLI-based, no GUI.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash on ASUSWRT/Merlin](https://github.com/MetaCubeX/Clash-for-Routers)|Router client for ASUS firmware.|runs on home routers, stable.|limited UI, technical setup.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash CLI (Linux/BSD)](https://github.com/Dreamacro/clash)|Command-line interface for advanced users.|lightweight, scriptable.|no GUI, requires configuration files.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Clash on Tomato / Mikrotik](https://github.com/MetaCubeX/Clash-for-Routers)|Embedded router solution.|centralized routing for home network.|firmware-specific, advanced setup.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS"
            "|[OpenWrt‑nikki](https://github.com/nikkinikki-org/OpenWrt-nikki)|OpenWRT router client for Clash.Meta, supports rule-based routing.|stable on routers, centralized proxy.|requires router with OpenWRT.|Clash.Meta.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
            "|[Mihomo Transparent Proxy (Docker)](https://github.com/scenery/mihomo-tproxy-docker)|Dockerized transparent proxy for any platform, easy deployment.|portable, cross-platform.|requires Docker knowledge.|Clash.Meta, Clash.|HTTP, HTTPS, SOCKS5, Shadowsocks, VMess, VLESS|",
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
            # جایگزینی URL
            modified = self._replace_proxy_url(original_template, url)
            new_path = f"./FCM_{subdir}_{idx + 1}.yml"
            modified = self._replace_proxy_path(modified, new_path)
    
            # مسیر کامل فایل خروجی
            output_path = os.path.join(output_subdir, filename)
    
            # اطمینان از پسوند .yml
            if not output_path.endswith(".yml"):
                logging.debug(f"⚠️ فایل {output_path} فاقد پسوند .yml است، اضافه شد")
                output_path += ".yml"
            else:
                logging.debug(f"✅ فایل {output_path} دارای پسوند .yml است")
            
            # بررسی و ساخت پوشه والد
            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                if os.path.isfile(parent_dir):
                    logging.warning(f"⚠️ یک فایل با نام پوشه وجود دارد و حذف می‌شود: {parent_dir}")
                    os.remove(parent_dir)
                if not os.path.exists(parent_dir):
                    logging.info(f"📂 ساخت پوشه والد: {parent_dir}")
                else:
                    logging.debug(f"✅ پوشه والد از قبل موجود است: {parent_dir}")
                os.makedirs(parent_dir, exist_ok=True)
        
            # نوشتن فایل
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(modified)
            logging.debug(f"📄 فایل ساخته شد: {output_path} (URL جایگزین شد)")
    
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
