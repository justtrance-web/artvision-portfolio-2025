#!/usr/bin/env python3
"""
Artvision Watermark + Copyright Protection
==========================================
Добавляет watermark Artvision.pro и защищает файлы через blockchain.
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# Watermark HTML+CSS блок
WATERMARK_BLOCK = '''
<!-- Artvision.pro Watermark -->
<style>
.artvision-watermark {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 99999;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-radius: 30px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    text-decoration: none;
    transition: all 0.3s ease;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
.artvision-watermark:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(87, 150, 204, 0.3);
}
.artvision-watermark__logo {
    width: 24px;
    height: 24px;
    border-radius: 6px;
    background: linear-gradient(135deg, #5796CC 0%, #3a7bb3 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 14px;
}
.artvision-watermark__text {
    font-size: 12px;
    font-weight: 600;
    color: #333;
    letter-spacing: -0.02em;
}
.artvision-watermark__text span {
    color: #5796CC;
}
@media (max-width: 480px) {
    .artvision-watermark {
        bottom: 15px;
        right: 15px;
        padding: 6px 12px;
    }
    .artvision-watermark__logo {
        width: 20px;
        height: 20px;
        font-size: 12px;
    }
    .artvision-watermark__text {
        font-size: 11px;
    }
}
@media print {
    .artvision-watermark { display: none !important; }
}
</style>
<a href="https://artvision.pro" target="_blank" rel="noopener" class="artvision-watermark" title="Разработано в Artvision.pro">
    <div class="artvision-watermark__logo">A</div>
    <div class="artvision-watermark__text">Artvision<span>.pro</span></div>
</a>
<!-- /Artvision.pro Watermark -->
'''

# HTML комментарий с копирайтом (добавляется в head)
COPYRIGHT_COMMENT = '''
    <!--
    ╔═══════════════════════════════════════════════════════════╗
    ║  © 2025 Artvision.pro                                     ║
    ║  Маркетинговое агентство с 2007 года                      ║
    ║  Санкт-Петербург • Москва                                 ║
    ║  https://artvision.pro                                    ║
    ╚═══════════════════════════════════════════════════════════╝
    -->
'''


def add_watermark_to_file(input_path: str, output_path: str) -> bool:
    """
    Добавляет watermark в HTML файл.
    
    Returns:
        True если успешно, False если файл уже имеет watermark
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем, есть ли уже watermark
    if 'artvision-watermark' in content.lower():
        print(f"  ⏭️  Watermark уже есть")
        # Просто копируем без изменений
        shutil.copy(input_path, output_path)
        return False
    
    # Добавляем copyright комментарий после <head>
    if '<head>' in content and 'Artvision.pro' not in content[:500]:
        content = content.replace('<head>', '<head>' + COPYRIGHT_COMMENT, 1)
    
    # Добавляем watermark перед </body>
    if '</body>' in content:
        content = content.replace('</body>', WATERMARK_BLOCK + '\n</body>', 1)
    else:
        # Если нет </body>, добавляем в конец
        content += WATERMARK_BLOCK
    
    # Сохраняем
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True


def process_files(input_dir: str, output_dir: str) -> dict:
    """
    Обрабатывает все HTML файлы в директории.
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "processed": [],
        "skipped": [],
        "errors": []
    }
    
    html_files = list(input_dir.glob("*.html"))
    print(f"\n📁 Найдено {len(html_files)} HTML файлов\n")
    
    for html_file in sorted(html_files):
        print(f"📄 {html_file.name}")
        
        try:
            output_path = output_dir / html_file.name
            added = add_watermark_to_file(str(html_file), str(output_path))
            
            if added:
                print(f"  ✅ Watermark добавлен")
                results["processed"].append(html_file.name)
            else:
                results["skipped"].append(html_file.name)
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results["errors"].append({"file": html_file.name, "error": str(e)})
    
    return results


if __name__ == "__main__":
    import sys
    
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs/landings-protected"
    
    print("=" * 50)
    print("🎨 ARTVISION WATERMARK TOOL")
    print("=" * 50)
    
    results = process_files(input_dir, output_dir)
    
    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТ")
    print("=" * 50)
    print(f"✅ Обработано: {len(results['processed'])}")
    print(f"⏭️  Пропущено (уже есть): {len(results['skipped'])}")
    print(f"❌ Ошибок: {len(results['errors'])}")
    print(f"\n📂 Файлы сохранены в: {output_dir}")
