#!/usr/bin/env python3
"""
Retry Blockchain Timestamps
===========================
Повторная попытка записи в blockchain для файлов,
которые были защищены только локально.

Использование:
    python retry_blockchain.py
"""

import json
import sys
from pathlib import Path

# Добавляем путь к модулю
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from copyright_protector import CopyrightProtector


def retry_pending_files(base_dir: str = None):
    """
    Находит файлы без blockchain timestamp и пытается записать.
    """
    if base_dir is None:
        base_dir = SCRIPT_DIR.parent
    
    protector = CopyrightProtector(str(base_dir))
    
    pending = []
    for entry in protector.registry["files"]:
        if entry["proofs"].get("blockchain") is None:
            pending.append(entry)
    
    if not pending:
        print("✅ Все файлы уже имеют blockchain timestamp!")
        return
    
    print(f"⏳ Найдено {len(pending)} файлов без blockchain timestamp\n")
    
    success = 0
    failed = 0
    
    for entry in pending:
        print(f"📄 {entry['file_name']}...")
        
        result = protector.create_timestamp_opentimestamps(
            entry["hash"],
            Path(entry["file_name"]).stem
        )
        
        if result:
            # Обновляем запись
            for i, e in enumerate(protector.registry["files"]):
                if e["id"] == entry["id"]:
                    protector.registry["files"][i]["proofs"]["blockchain"] = result
                    break
            
            print(f"   ✅ Записано в {result['blockchain']}")
            success += 1
        else:
            print(f"   ❌ Не удалось (сервис недоступен)")
            failed += 1
    
    # Сохраняем обновлённый реестр
    protector._save_registry()
    
    print(f"\n{'='*40}")
    print(f"Успешно: {success}")
    print(f"Не удалось: {failed}")
    
    if failed > 0:
        print("\n💡 Совет: повторите позже, когда OpenTimestamps будет доступен")


if __name__ == "__main__":
    retry_pending_files()
