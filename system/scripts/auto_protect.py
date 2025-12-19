#!/usr/bin/env python3
"""
Artvision Auto-Protect Hook
===========================
Автоматическая защита HTML-лендингов после создания.

Использование в Claude:
После создания HTML-файла вызвать:
    python auto_protect.py /path/to/landing.html --project "Название" --client "Клиент"

Или для папки:
    python auto_protect.py /path/to/folder/ --project "Портфолио"
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем путь к основному модулю
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from copyright_protector import CopyrightProtector


def auto_protect(
    path: str,
    project: str = None,
    client: str = None,
    description: str = None,
    base_dir: str = None
) -> dict:
    """
    Автоматическая защита файла или папки.
    
    Args:
        path: Путь к файлу или папке
        project: Название проекта
        client: Название клиента
        description: Описание
        base_dir: Базовая директория системы copyright
    
    Returns:
        dict с результатами защиты
    """
    # Определяем базовую директорию
    if base_dir is None:
        base_dir = SCRIPT_DIR.parent
    
    protector = CopyrightProtector(str(base_dir))
    
    path = Path(path)
    results = {
        "timestamp": datetime.now().isoformat(),
        "protected": [],
        "skipped": [],
        "errors": []
    }
    
    if path.is_file():
        try:
            entry = protector.protect_file(
                str(path),
                project_name=project,
                client_name=client,
                description=description
            )
            results["protected"].append({
                "file": path.name,
                "id": entry["id"],
                "hash": entry["hash"][:16] + "..."
            })
        except Exception as e:
            results["errors"].append({
                "file": path.name,
                "error": str(e)
            })
    
    elif path.is_dir():
        # Защищаем все HTML файлы в папке
        for html_file in path.glob("**/*.html"):
            # Пропускаем служебные файлы
            if any(skip in str(html_file) for skip in ["node_modules", ".git", "__pycache__"]):
                results["skipped"].append(str(html_file))
                continue
            
            try:
                entry = protector.protect_file(
                    str(html_file),
                    project_name=project,
                    client_name=client,
                    description=description
                )
                results["protected"].append({
                    "file": html_file.name,
                    "id": entry["id"],
                    "hash": entry["hash"][:16] + "..."
                })
            except Exception as e:
                results["errors"].append({
                    "file": html_file.name,
                    "error": str(e)
                })
    
    # Выводим сводку
    print("\n" + "=" * 50)
    print("📊 СВОДКА ЗАЩИТЫ")
    print("=" * 50)
    print(f"✅ Защищено: {len(results['protected'])} файлов")
    if results["skipped"]:
        print(f"⏭️  Пропущено: {len(results['skipped'])} файлов")
    if results["errors"]:
        print(f"❌ Ошибок: {len(results['errors'])}")
    
    return results


def quick_protect(file_path: str, project: str = "Auto-protected"):
    """
    Быстрая защита одного файла без лишних параметров.
    Для использования как однострочник.
    """
    return auto_protect(file_path, project=project)


# CLI интерфейс
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Автозащита HTML-лендингов Artvision"
    )
    parser.add_argument("path", help="Путь к файлу или папке")
    parser.add_argument("--project", "-p", help="Название проекта")
    parser.add_argument("--client", "-c", help="Название клиента")
    parser.add_argument("--description", "-d", help="Описание")
    parser.add_argument("--base-dir", help="Базовая директория системы")
    
    args = parser.parse_args()
    
    results = auto_protect(
        args.path,
        project=args.project,
        client=args.client,
        description=args.description,
        base_dir=args.base_dir
    )
    
    # Выход с кодом ошибки если были проблемы
    if results["errors"]:
        sys.exit(1)
