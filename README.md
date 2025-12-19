# Artvision Portfolio & System Backup

Публичный архив работ Artvision.pro с защитой авторских прав + бэкап всех настроек и скриптов.

## 📁 Структура

```
artvision-portfolio-2025/
│
├── portfolio/                    # 🎨 Работы по категориям
│   ├── dental/                   # Стоматология (6 лендингов)
│   ├── promo/                    # Промо-лендинги (4)
│   ├── exhibitions/              # Выставки (1)
│   └── reports/                  # Отчёты (1)
│
├── system/                       # ⚙️ Системные файлы
│   ├── scripts/                  # Python скрипты
│   ├── memory-rules/             # Правила Claude (25 правил)
│   └── skills-backup/            # Бэкап всех skills (20 шт)
│
├── proofs/                       # 🔐 Proof-файлы SHA-256
│
├── registry.json                 # Реестр защищённых файлов
└── index.html                    # Каталог с превью
```

## 🔗 Прямой доступ (GitHub Pages)

**Каталог:** https://justtrance-web.github.io/artvision-portfolio-2025/

### Примеры:
- [OTIDO Выставочные стенды](https://justtrance-web.github.io/artvision-portfolio-2025/portfolio/exhibitions/otido-landing-v5.html)
- [Alfa Clinic Bold](https://justtrance-web.github.io/artvision-portfolio-2025/portfolio/dental/alfa-clinic-bold.html)
- [VLP Gift Box](https://justtrance-web.github.io/artvision-portfolio-2025/portfolio/promo/vlp-giftbox-final.html)
- [ТМК Годовой отчёт](https://justtrance-web.github.io/artvision-portfolio-2025/portfolio/reports/tmk-annual-report-2024.html)

## 🔐 Защита авторства

Все файлы защищены:
- **SHA-256 хеш** — уникальный отпечаток
- **JSON proof** — метаданные + timestamp
- **Git history** — дополнительное доказательство даты

### Верификация:
```bash
sha256sum portfolio/dental/alfa-clinic-bold.html
# Сравнить с proofs/alfa-clinic-bold_*.json
```

## 📦 Содержимое

### Portfolio (12 лендингов)

| Категория | Файлов | Описание |
|-----------|--------|----------|
| dental | 6 | Стоматология: Alfa Clinic, All-on-4 |
| promo | 4 | VLP Gift Box промо |
| exhibitions | 1 | OTIDO выставочные стенды |
| reports | 1 | ТМК годовой отчёт 2024 |

### System (бэкап)

| Раздел | Файлов | Описание |
|--------|--------|----------|
| scripts | 4 | copyright_protector, watermark, auto_protect |
| memory-rules | 1 | 25 правил Claude |
| skills-backup | 20 | SEO, frontend, auth, и др. |

## 🛠 Скрипты

### Защита авторства
```bash
python system/scripts/auto_protect.py landing.html -p "Проект"
```

### Добавление watermark
```bash
python system/scripts/add_watermark.py input.html output.html
```

### Проверка файла
```bash
python system/scripts/copyright_protector.py verify file.html
```

## 📜 Memory Rules

25 правил для Claude сохранены в `system/memory-rules/claude-memory-rules.md`:
- SEO автоматизация
- HTML/CSS стандарты
- Asana интеграция
- Blockchain protection
- И другие...

## 🔗 Контакты

- **Сайт:** [artvision.pro](https://artvision.pro)
- **Email:** anton@artvision.pro
- **Telegram:** @justtrance

---

© 2025 Artvision.pro | Санкт-Петербург • Москва | С 2007 года
