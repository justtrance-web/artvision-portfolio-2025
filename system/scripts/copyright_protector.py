#!/usr/bin/env python3
"""
Artvision Copyright Protector
============================
Система защиты авторских прав на HTML-лендинги через blockchain timestamping.

Использует:
- SHA-256 хеширование файлов
- OpenTimestamps (Bitcoin blockchain)
- Локальное хранилище доказательств

Автор: Artvision.pro
"""

import hashlib
import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
import base64


class CopyrightProtector:
    """Защита авторских прав через blockchain timestamping."""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.dirname(os.path.dirname(__file__)))
        self.proofs_dir = self.base_dir / "proofs"
        self.logs_dir = self.base_dir / "logs"
        self.registry_file = self.base_dir / "registry.json"
        
        # Создаём директории
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Загружаем реестр
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Загрузка реестра зарегистрированных файлов."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": [], "metadata": {"created": datetime.now().isoformat()}}
    
    def _save_registry(self):
        """Сохранение реестра."""
        self.registry["metadata"]["updated"] = datetime.now().isoformat()
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    def calculate_hash(self, file_path: str) -> str:
        """Вычисление SHA-256 хеша файла."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def calculate_content_hash(self, content: str) -> str:
        """Вычисление SHA-256 хеша строки."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def create_timestamp_opentimestamps(self, file_hash: str, file_name: str) -> Optional[Dict]:
        """
        Создание timestamp через OpenTimestamps (бесплатно, Bitcoin blockchain).
        
        OpenTimestamps записывает хеш в Bitcoin blockchain.
        Верификация: https://opentimestamps.org/
        """
        try:
            # Создаём .ots файл (OpenTimestamps proof)
            hash_bytes = bytes.fromhex(file_hash)
            
            # OpenTimestamps API
            url = "https://a.pool.opentimestamps.org/digest"
            
            req = urllib.request.Request(
                url,
                data=hash_bytes,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/vnd.opentimestamps.v1'
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                ots_data = response.read()
                
                # Сохраняем .ots proof файл
                ots_filename = f"{file_name}_{file_hash[:16]}.ots"
                ots_path = self.proofs_dir / ots_filename
                
                with open(ots_path, 'wb') as f:
                    f.write(ots_data)
                
                return {
                    "service": "OpenTimestamps",
                    "blockchain": "Bitcoin",
                    "ots_file": str(ots_path),
                    "verification_url": "https://opentimestamps.org/",
                    "status": "pending_confirmation",
                    "note": "Подтверждение в блокчейне Bitcoin занимает ~2 часа"
                }
                
        except urllib.error.URLError as e:
            print(f"⚠️  OpenTimestamps недоступен: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Ошибка OpenTimestamps: {e}")
            return None
    
    def create_local_proof(self, file_path: str, file_hash: str) -> Dict:
        """
        Создание локального proof-файла (резервный метод).
        Может использоваться как доказательство в суде.
        """
        file_path = Path(file_path)
        
        # Читаем содержимое файла
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Формируем proof
        proof = {
            "version": "1.0",
            "type": "copyright_proof",
            "author": "Artvision.pro",
            "author_details": {
                "company": "Маркетинговое агентство Artvision",
                "location": "Санкт-Петербург, Москва",
                "website": "https://artvision.pro",
                "since": 2007
            },
            "file": {
                "name": file_path.name,
                "original_path": str(file_path.absolute()),
                "size_bytes": file_path.stat().st_size,
                "hash_algorithm": "SHA-256",
                "hash": file_hash
            },
            "timestamp": {
                "created": datetime.now().isoformat(),
                "timezone": "Europe/Moscow",
                "unix": int(datetime.now().timestamp())
            },
            "content_fingerprint": {
                "first_100_chars_hash": self.calculate_content_hash(content[:100]),
                "last_100_chars_hash": self.calculate_content_hash(content[-100:]),
                "total_lines": content.count('\n') + 1,
                "total_chars": len(content)
            }
        }
        
        # Сохраняем proof
        proof_filename = f"{file_path.stem}_{file_hash[:16]}_proof.json"
        proof_path = self.proofs_dir / proof_filename
        
        with open(proof_path, 'w', encoding='utf-8') as f:
            json.dump(proof, f, ensure_ascii=False, indent=2)
        
        return {
            "proof_file": str(proof_path),
            "proof_hash": self.calculate_content_hash(json.dumps(proof, sort_keys=True))
        }
    
    def protect_file(self, file_path: str, project_name: str = None, 
                     client_name: str = None, description: str = None) -> Dict:
        """
        Полная защита файла: хеширование + blockchain + локальный proof.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        print(f"\n🔐 Защита файла: {file_path.name}")
        print("=" * 50)
        
        # 1. Вычисляем хеш
        file_hash = self.calculate_hash(str(file_path))
        print(f"📊 SHA-256: {file_hash}")
        
        # 2. Проверяем, не зарегистрирован ли уже
        for entry in self.registry["files"]:
            if entry["hash"] == file_hash:
                print(f"✅ Файл уже зарегистрирован: {entry['registered_at']}")
                return entry
        
        # 3. Создаём локальный proof
        local_proof = self.create_local_proof(str(file_path), file_hash)
        print(f"📄 Локальный proof: {local_proof['proof_file']}")
        
        # 4. OpenTimestamps (Bitcoin blockchain)
        print("⏳ Отправка в Bitcoin blockchain...")
        blockchain_proof = self.create_timestamp_opentimestamps(file_hash, file_path.stem)
        
        if blockchain_proof:
            print(f"✅ OpenTimestamps: {blockchain_proof['ots_file']}")
        else:
            print("⚠️  Blockchain timestamp не создан (offline mode)")
        
        # 5. Формируем запись реестра
        entry = {
            "id": len(self.registry["files"]) + 1,
            "file_name": file_path.name,
            "original_path": str(file_path.absolute()),
            "hash": file_hash,
            "hash_algorithm": "SHA-256",
            "registered_at": datetime.now().isoformat(),
            "project": project_name,
            "client": client_name,
            "description": description,
            "proofs": {
                "local": local_proof,
                "blockchain": blockchain_proof
            },
            "status": "protected"
        }
        
        self.registry["files"].append(entry)
        self._save_registry()
        
        print(f"\n✅ Файл защищён! ID: {entry['id']}")
        return entry
    
    def protect_directory(self, dir_path: str, pattern: str = "*.html", **kwargs) -> List[Dict]:
        """Защита всех файлов в директории по паттерну."""
        dir_path = Path(dir_path)
        results = []
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                try:
                    result = self.protect_file(str(file_path), **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"❌ Ошибка с {file_path}: {e}")
        
        return results
    
    def verify_file(self, file_path: str) -> Dict:
        """Проверка файла по реестру."""
        file_hash = self.calculate_hash(file_path)
        
        for entry in self.registry["files"]:
            if entry["hash"] == file_hash:
                return {
                    "verified": True,
                    "message": "Файл найден в реестре",
                    "entry": entry
                }
        
        return {
            "verified": False,
            "message": "Файл НЕ найден в реестре",
            "current_hash": file_hash
        }
    
    def generate_report(self) -> str:
        """Генерация отчёта по всем защищённым файлам."""
        report = []
        report.append("=" * 60)
        report.append("ARTVISION COPYRIGHT REGISTRY")
        report.append(f"Дата отчёта: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        report.append("=" * 60)
        report.append("")
        
        for entry in self.registry["files"]:
            report.append(f"ID: {entry['id']}")
            report.append(f"Файл: {entry['file_name']}")
            report.append(f"SHA-256: {entry['hash']}")
            report.append(f"Дата регистрации: {entry['registered_at']}")
            if entry.get('project'):
                report.append(f"Проект: {entry['project']}")
            if entry.get('client'):
                report.append(f"Клиент: {entry['client']}")
            
            # Blockchain status
            if entry['proofs'].get('blockchain'):
                bc = entry['proofs']['blockchain']
                report.append(f"Blockchain: {bc['blockchain']} ({bc['service']})")
            
            report.append("-" * 40)
            report.append("")
        
        report.append(f"Всего защищённых файлов: {len(self.registry['files'])}")
        
        return "\n".join(report)
    
    def export_proof_package(self, file_id: int, output_dir: str = None) -> str:
        """
        Экспорт полного пакета доказательств для конкретного файла.
        Используется для предоставления в суде или клиенту.
        """
        entry = None
        for e in self.registry["files"]:
            if e["id"] == file_id:
                entry = e
                break
        
        if not entry:
            raise ValueError(f"Файл с ID {file_id} не найден")
        
        output_dir = Path(output_dir or self.proofs_dir / "packages")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        package_name = f"copyright_proof_{entry['file_name']}_{entry['hash'][:8]}"
        package_dir = output_dir / package_name
        package_dir.mkdir(exist_ok=True)
        
        # Копируем все proof файлы
        import shutil
        
        if entry['proofs'].get('local', {}).get('proof_file'):
            shutil.copy(entry['proofs']['local']['proof_file'], package_dir)
        
        if entry['proofs'].get('blockchain', {}).get('ots_file'):
            shutil.copy(entry['proofs']['blockchain']['ots_file'], package_dir)
        
        # Создаём сводный документ
        summary = {
            "title": "СВИДЕТЕЛЬСТВО О ЗАЩИТЕ АВТОРСКИХ ПРАВ",
            "document_type": "copyright_proof_package",
            "generated_at": datetime.now().isoformat(),
            "entry": entry,
            "instructions": {
                "verification": [
                    "1. Вычислите SHA-256 хеш исходного файла",
                    "2. Сравните с хешем в этом документе",
                    "3. Для blockchain-верификации используйте https://opentimestamps.org/",
                    "4. Загрузите .ots файл для проверки"
                ]
            },
            "legal_notice": (
                "Данный пакет документов подтверждает факт существования файла "
                f"'{entry['file_name']}' на дату {entry['registered_at']}. "
                "Хеш-сумма файла зафиксирована в блокчейне Bitcoin через сервис OpenTimestamps."
            )
        }
        
        summary_path = package_dir / "SUMMARY.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print(f"📦 Пакет доказательств создан: {package_dir}")
        return str(package_dir)


def main():
    """CLI интерфейс."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Artvision Copyright Protector")
    parser.add_argument("action", choices=["protect", "verify", "report", "export"],
                       help="Действие: protect/verify/report/export")
    parser.add_argument("path", nargs="?", help="Путь к файлу или директории")
    parser.add_argument("--project", help="Название проекта")
    parser.add_argument("--client", help="Название клиента")
    parser.add_argument("--description", help="Описание")
    parser.add_argument("--id", type=int, help="ID файла для экспорта")
    parser.add_argument("--base-dir", help="Базовая директория для хранения")
    
    args = parser.parse_args()
    
    protector = CopyrightProtector(args.base_dir)
    
    if args.action == "protect":
        if not args.path:
            print("Укажите путь к файлу или директории")
            sys.exit(1)
        
        path = Path(args.path)
        if path.is_file():
            protector.protect_file(str(path), args.project, args.client, args.description)
        elif path.is_dir():
            protector.protect_directory(str(path), project_name=args.project, 
                                        client_name=args.client, description=args.description)
        else:
            print(f"Путь не найден: {path}")
            sys.exit(1)
    
    elif args.action == "verify":
        if not args.path:
            print("Укажите путь к файлу")
            sys.exit(1)
        result = protector.verify_file(args.path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif args.action == "report":
        print(protector.generate_report())
    
    elif args.action == "export":
        if not args.id:
            print("Укажите --id файла для экспорта")
            sys.exit(1)
        protector.export_proof_package(args.id)


if __name__ == "__main__":
    main()
