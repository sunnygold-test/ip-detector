"""Минимальный тест Яндекс.Диска — пошагово."""
import os
import json
import requests

TOKEN = os.environ.get("YANDEX_DISK_TOKEN")

if not TOKEN:
    print("НЕТ ТОКЕНА!")
    exit(1)

print(f"Токен: длина={len(TOKEN)}, начало={TOKEN[:8]}..., конец=...{TOKEN[-8:]}")
print(f"Есть пробелы: {' ' in TOKEN}")
print(f"Есть переводы строк: {chr(10) in TOKEN or chr(13) in TOKEN}")

HEADERS = {"Authorization": f"OAuth {TOKEN}"}
API = "https://cloud-api.yandex.net/v1/disk/resources"


def show(label, resp):
    """Печатает статус и тело ответа."""
    print(f"\n=== {label} ===")
    print(f"URL: {resp.url}")
    print(f"Статус: {resp.status_code}")
    print(f"Ответ: {resp.text[:500]}")


# 1. Информация о диске
r = requests.get("https://cloud-api.yandex.net/v1/disk/", headers=HEADERS)
show("1. Информация о диске", r)

if r.status_code != 200:
    print("\n❌ Токен не работает, дальше нет смысла.")
    exit(1)

# 2. Создание папки
FOLDER = "ip_detector"
r = requests.put(API, headers=HEADERS, params={"path": FOLDER})
show("2. Создание папки", r)

# 3. Получение ссылки для загрузки
REMOTE = f"{FOLDER}/ip_info.json"
r = requests.get(f"{API}/upload", headers=HEADERS,
                 params={"path": REMOTE, "overwrite": "true"})
show("3. Ссылка на загрузку", r)

if r.status_code != 200:
    print("\n❌ Не удалось получить ссылку на загрузку.")
    exit(1)

# 4. Загрузка файла
upload_url = r.json()["href"]
data = json.dumps({"test": "hello"}, ensure_ascii=False).encode("utf-8")
r = requests.put(upload_url, data=data)
show("4. Загрузка файла", r)

if r.status_code not in (200, 201):
    print("\n❌ Ошибка при загрузке.")
    exit(1)

# 5. Проверка, что файл есть
r = requests.get(API, headers=HEADERS, params={"path": REMOTE})
show("5. Проверка файла", r)

if r.status_code == 200:
    info = r.json()
    print(f"\n✅ ФАЙЛ НА МЕСТЕ: {info.get('name')}, "
          f"размер {info.get('size')} байт")
    print(f"Ссылка: https://disk.yandex.ru/client/disk/{REMOTE}")
else:
    print(f"\n❌ Файл не найден. Статус: {r.status_code}")