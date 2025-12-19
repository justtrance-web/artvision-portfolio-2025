#!/usr/bin/env python3
"""
Brand Extractor v1.1
=====================
Извлекает брендовые элементы с сайта:
- Цветовая палитра (HEX, RGB, HSL)
- Шрифты (font-family)
- Размеры (border-radius, spacing)
- Логотип
- Градиенты
- Тени

Использование:
    python brand_extractor.py https://example.com
    python brand_extractor.py https://example.com --output brand.json
    python brand_extractor.py https://example.com --format md
"""

import requests
import re
import json
import sys
import argparse
from collections import Counter
from urllib.parse import urljoin, urlparse
from datetime import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Установите: pip install beautifulsoup4 --break-system-packages")
    sys.exit(1)

import warnings
warnings.filterwarnings('ignore')


class BrandExtractor:
    def __init__(self, url):
        self.url = url
        self.base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        self.domain = urlparse(url).netloc.replace('www.', '')
        self.html = ""
        self.css_content = ""
        self.soup = None
        self.brand = {
            "url": url,
            "domain": self.domain,
            "extracted_at": datetime.now().isoformat(),
            "colors": {
                "primary": [],
                "all": [],
                "by_frequency": []
            },
            "fonts": {
                "families": [],
                "sizes": []
            },
            "spacing": {
                "border_radius": [],
                "paddings": [],
                "margins": []
            },
            "effects": {
                "gradients": [],
                "shadows": []
            },
            "assets": {
                "logo": None,
                "favicon": None,
                "images": []
            },
            "meta": {
                "title": "",
                "description": "",
                "keywords": []
            }
        }
        
    def fetch(self, url):
        """Скачивает контент по URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            r = requests.get(url, headers=headers, timeout=30, verify=False)
            r.encoding = r.apparent_encoding
            return r.text
        except Exception as e:
            print(f"  ⚠️ Ошибка загрузки {url}: {e}")
            return ""
    
    def _collect_css(self):
        """Собирает весь CSS со страницы"""
        print("📥 Собираю CSS...")
        
        # Inline styles
        for tag in self.soup.find_all(style=True):
            self.css_content += tag['style'] + "\n"
        
        # <style> теги
        for style in self.soup.find_all('style'):
            if style.string:
                self.css_content += style.string + "\n"
        
        # Внешние CSS файлы (первые 5)
        links = self.soup.find_all('link', rel='stylesheet')[:5]
        for link in links:
            href = link.get('href')
            if href:
                css_url = urljoin(self.base_url, href)
                css = self.fetch(css_url)
                if css:
                    self.css_content += css + "\n"
                    print(f"   ✅ {href[:50]}...")
        
        print(f"   📊 Всего CSS: {len(self.css_content):,} символов")
    
    def _extract_colors(self):
        """Извлекает цвета"""
        print("🎨 Извлекаю цвета...")
        
        colors = []
        
        # HEX цвета
        hex_pattern = r'#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})\b'
        hex_colors = re.findall(hex_pattern, self.css_content)
        for c in hex_colors:
            if len(c) == 3:
                c = c[0]*2 + c[1]*2 + c[2]*2
            colors.append(f"#{c.upper()}")
        
        # RGB/RGBA
        rgb_pattern = r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
        rgb_colors = re.findall(rgb_pattern, self.css_content)
        for r, g, b in rgb_colors:
            hex_color = f"#{int(r):02X}{int(g):02X}{int(b):02X}"
            colors.append(hex_color)
        
        # HSL
        hsl_pattern = r'hsla?\s*\(\s*(\d+)\s*,\s*(\d+)%?\s*,\s*(\d+)%?'
        hsl_colors = re.findall(hsl_pattern, self.css_content)
        for h, s, l in hsl_colors:
            # Простая конвертация HSL -> HEX
            colors.append(f"hsl({h},{s}%,{l}%)")
        
        # Подсчёт частоты
        color_counts = Counter(colors)
        
        # Фильтруем чёрный, белый и серые
        filtered = []
        for color, count in color_counts.most_common(50):
            if color.startswith('#'):
                # Пропускаем чисто чёрный/белый и близкие к ним
                if color.upper() not in ['#FFFFFF', '#000000', '#FFF', '#000']:
                    # Проверяем на серый
                    if len(color) == 7:
                        r = int(color[1:3], 16)
                        g = int(color[3:5], 16)
                        b = int(color[5:7], 16)
                        if not (abs(r-g) < 10 and abs(g-b) < 10 and abs(r-b) < 10):
                            filtered.append({"color": color, "count": count})
            else:
                filtered.append({"color": color, "count": count})
        
        self.brand["colors"]["by_frequency"] = filtered[:20]
        self.brand["colors"]["all"] = list(set([c["color"] for c in filtered]))
        
        # Первые 3-5 цветов как primary
        self.brand["colors"]["primary"] = [c["color"] for c in filtered[:5]]
        
        print(f"   ✅ Найдено: {len(filtered)} уникальных цветов")
    
    def _extract_fonts(self):
        """Извлекает шрифты"""
        print("🔤 Извлекаю шрифты...")
        
        # font-family
        font_pattern = r'font-family\s*:\s*([^;}\n]+)'
        fonts = re.findall(font_pattern, self.css_content, re.IGNORECASE)
        
        font_families = []
        for font in fonts:
            # Чистим и разбиваем
            font = font.strip().strip('"\'')
            families = [f.strip().strip('"\'') for f in font.split(',')]
            for f in families:
                if f and f.lower() not in ['inherit', 'initial', 'unset', 'serif', 'sans-serif', 'monospace']:
                    font_families.append(f)
        
        font_counts = Counter(font_families)
        self.brand["fonts"]["families"] = [
            {"font": f, "count": c} 
            for f, c in font_counts.most_common(10)
        ]
        
        # font-size
        size_pattern = r'font-size\s*:\s*([^;}\n]+)'
        sizes = re.findall(size_pattern, self.css_content, re.IGNORECASE)
        size_counts = Counter([s.strip() for s in sizes])
        self.brand["fonts"]["sizes"] = [
            {"size": s, "count": c}
            for s, c in size_counts.most_common(15)
        ]
        
        print(f"   ✅ Шрифтов: {len(font_counts)}, размеров: {len(size_counts)}")
    
    def _extract_spacing(self):
        """Извлекает отступы и радиусы"""
        print("📐 Извлекаю spacing...")
        
        # border-radius
        br_pattern = r'border-radius\s*:\s*([^;}\n]+)'
        br = re.findall(br_pattern, self.css_content, re.IGNORECASE)
        br_counts = Counter([b.strip() for b in br])
        self.brand["spacing"]["border_radius"] = [
            {"value": v, "count": c}
            for v, c in br_counts.most_common(10)
        ]
        
        # padding
        pad_pattern = r'padding\s*:\s*([^;}\n]+)'
        pads = re.findall(pad_pattern, self.css_content, re.IGNORECASE)
        pad_counts = Counter([p.strip() for p in pads if 'var(' not in p])
        self.brand["spacing"]["paddings"] = [
            {"value": v, "count": c}
            for v, c in pad_counts.most_common(10)
        ]
        
        print(f"   ✅ border-radius: {len(br_counts)}, paddings: {len(pad_counts)}")
    
    def _extract_effects(self):
        """Извлекает градиенты и тени"""
        print("✨ Извлекаю эффекты...")
        
        # Градиенты
        grad_pattern = r'(linear-gradient|radial-gradient)\s*\([^)]+\)'
        gradients = re.findall(grad_pattern, self.css_content, re.IGNORECASE)
        grad_full = re.findall(r'((?:linear|radial)-gradient\s*\([^)]+\))', self.css_content, re.IGNORECASE)
        self.brand["effects"]["gradients"] = list(set(grad_full))[:10]
        
        # Тени
        shadow_pattern = r'box-shadow\s*:\s*([^;}\n]+)'
        shadows = re.findall(shadow_pattern, self.css_content, re.IGNORECASE)
        shadow_counts = Counter([s.strip() for s in shadows if s.strip() != 'none'])
        self.brand["effects"]["shadows"] = [
            {"value": v, "count": c}
            for v, c in shadow_counts.most_common(5)
        ]
        
        print(f"   ✅ Градиентов: {len(self.brand['effects']['gradients'])}, теней: {len(shadow_counts)}")
    
    def _extract_assets(self):
        """Извлекает логотип и favicon"""
        print("🖼️ Извлекаю ассеты...")
        
        # Favicon
        favicon = self.soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if favicon:
            self.brand["assets"]["favicon"] = urljoin(self.base_url, favicon.get('href', ''))
        
        # Логотип (эвристика)
        logo = None
        
        # Ищем по классу/id
        logo_selectors = [
            ('img', {'class': re.compile(r'logo', re.I)}),
            ('img', {'id': re.compile(r'logo', re.I)}),
            ('img', {'alt': re.compile(r'logo', re.I)}),
            ('img', {'src': re.compile(r'logo', re.I)}),
        ]
        
        for tag, attrs in logo_selectors:
            found = self.soup.find(tag, attrs)
            if found and found.get('src'):
                logo = urljoin(self.base_url, found['src'])
                break
        
        # Ищем в header
        if not logo:
            header = self.soup.find(['header', 'nav'])
            if header:
                img = header.find('img')
                if img and img.get('src'):
                    logo = urljoin(self.base_url, img['src'])
        
        self.brand["assets"]["logo"] = logo
        
        print(f"   ✅ Logo: {'найден' if logo else 'не найден'}, Favicon: {'найден' if favicon else 'не найден'}")
    
    def _extract_meta(self):
        """Извлекает мета-данные"""
        print("📝 Извлекаю meta...")
        
        # Title
        title = self.soup.find('title')
        self.brand["meta"]["title"] = title.string.strip() if title and title.string else ""
        
        # Description
        desc = self.soup.find('meta', attrs={'name': 'description'})
        self.brand["meta"]["description"] = desc.get('content', '') if desc else ""
        
        # Keywords
        kw = self.soup.find('meta', attrs={'name': 'keywords'})
        if kw and kw.get('content'):
            self.brand["meta"]["keywords"] = [k.strip() for k in kw['content'].split(',')]
        
        print(f"   ✅ Title: {len(self.brand['meta']['title'])} символов")
    
    def extract_all(self):
        """Главный метод - извлекает всё"""
        print(f"\n{'='*60}")
        print(f"🔍 BRAND EXTRACTOR v1.1")
        print(f"{'='*60}")
        print(f"URL: {self.url}")
        print(f"{'='*60}\n")
        
        # 1. Скачиваем HTML
        print("📥 Скачиваю HTML...")
        self.html = self.fetch(self.url)
        if not self.html:
            return {"error": "Не удалось загрузить страницу"}
        print(f"   ✅ HTML: {len(self.html):,} символов")
        
        self.soup = BeautifulSoup(self.html, 'html.parser')
        
        # 2. Собираем CSS
        self._collect_css()
        
        # 3. Извлекаем данные
        self._extract_colors()
        self._extract_fonts()
        self._extract_spacing()
        self._extract_effects()
        self._extract_assets()
        self._extract_meta()
        
        print(f"\n{'='*60}")
        print("✅ ИЗВЛЕЧЕНИЕ ЗАВЕРШЕНО")
        print(f"{'='*60}\n")
        
        return self.brand
    
    def to_json(self, indent=2):
        """Возвращает JSON"""
        return json.dumps(self.brand, indent=indent, ensure_ascii=False)
    
    def to_markdown(self):
        """Возвращает Markdown отчёт"""
        b = self.brand
        md = f"""# Brand Book: {b['domain']}

**URL:** {b['url']}  
**Дата извлечения:** {b['extracted_at']}

---

## 🎨 Цвета

### Primary (основные)
{chr(10).join([f'- `{c}`' for c in b['colors']['primary'][:5]])}

### По частоте использования
| Цвет | Использований |
|------|---------------|
{chr(10).join([f"| `{c['color']}` | {c['count']} |" for c in b['colors']['by_frequency'][:10]])}

---

## 🔤 Шрифты

### Font Families
{chr(10).join([f"- **{f['font']}** ({f['count']} раз)" for f in b['fonts']['families'][:5]])}

### Font Sizes
{chr(10).join([f"- `{s['size']}` ({s['count']} раз)" for s in b['fonts']['sizes'][:8]])}

---

## 📐 Spacing

### Border Radius
{chr(10).join([f"- `{r['value']}`" for r in b['spacing']['border_radius'][:5]])}

---

## ✨ Эффекты

### Градиенты
{chr(10).join([f"```css{chr(10)}{g}{chr(10)}```" for g in b['effects']['gradients'][:3]]) if b['effects']['gradients'] else '_Не найдены_'}

### Тени (box-shadow)
{chr(10).join([f"```css{chr(10)}{s['value']}{chr(10)}```" for s in b['effects']['shadows'][:3]]) if b['effects']['shadows'] else '_Не найдены_'}

---

## 🖼️ Ассеты

- **Logo:** {b['assets']['logo'] or '_Не найден_'}
- **Favicon:** {b['assets']['favicon'] or '_Не найден_'}

---

## 📝 Meta

- **Title:** {b['meta']['title']}
- **Description:** {b['meta']['description'][:200]}...

---

_Сгенерировано Brand Extractor v1.1 | Artvision.pro_
"""
        return md


def main():
    parser = argparse.ArgumentParser(description='Brand Extractor - извлекает брендовые элементы с сайта')
    parser.add_argument('url', help='URL сайта для анализа')
    parser.add_argument('--output', '-o', help='Файл для сохранения результата')
    parser.add_argument('--format', '-f', choices=['json', 'md'], default='json', help='Формат вывода')
    
    args = parser.parse_args()
    
    extractor = BrandExtractor(args.url)
    brand = extractor.extract_all()
    
    if "error" in brand:
        print(f"❌ Ошибка: {brand['error']}")
        sys.exit(1)
    
    # Выводим результат
    if args.format == 'md':
        output = extractor.to_markdown()
    else:
        output = extractor.to_json()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"💾 Сохранено в {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
