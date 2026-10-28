import os
import json
import logging
import requests

# Настройка логирования для отслеживания процесса выполнения
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IpifyClient:
    """Класс для получения публичного IP-адреса через сервис ipify."""

    def __init__(self):
        self.api_url = "https://api.ipify.org?format=json"

    def get_public_ip(self):
        """Отправляет GET-запрос и возвращает строку с IP-адресом."""
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            return response.json().get("ip")
        except requests.RequestException as e:
            logging.error(f"Ошибка при получении IP: {e}")
            raise


class IpInfoClient:
    """Класс для получения геоданных через сервис ipinfo."""

    def __init__(self):
        self.base_url = "https://ipinfo.io"

    def get_geo_info(self, ip_address):
        """Запрашивает геоинформацию по указанному IP."""
        url = f"{self.base_url}/{ip_address}/geo"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Ошибка при получении геоданных: {e}")
            raise


class YandexDiskClient:
    """Класс для работы с REST API Яндекс.Диска."""

    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json"
        }
        self.api_base = "https://cloud-api.yandex.net/v1/disk/resources"

    def create_folder(self, folder_name):
        """Создает папку на Яндекс.Диске. Если папка существует, ошибка игнорируется."""
        params = {"path": f"/{folder_name}"}
        try:
            response = requests.put(self.api_base, headers=self.headers, params=params, timeout=10)
            # 409 Conflict означает, что папка уже существует, это допустимо
            if response.status_code == 409:
                logging.info(f"Папка '{folder_name}' уже существует.")
            else:
                response.raise_for_status()
                logging.info(f"Папка '{folder_name}' успешно создана.")
        except requests.RequestException as e:
            logging.error(f"Ошибка при создании папки: {e}")
            raise

    def upload_file_from_memory(self, folder_name, file_name, content_bytes):
        """
        Загружает файл на Диск, используя поток байтов в памяти.
        Это позволяет избежать создания локального файла на компьютере.
        """
        # 1. Получаем ссылку для загрузки
        upload_url_api = f"{self.api_base}/upload"
        remote_path = f"/{folder_name}/{file_name}"
        params = {"path": remote_path, "overwrite": "true"}

        try:
            # Запрос ссылки на загрузку
            response = requests.get(upload_url_api, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            upload_href = response.json().get("href")

            # 2. Выполняем PUT-запрос на полученный href с байтами файла
            # Заголовок Authorization здесь не нужен, так как ссылка уже подписана
            upload_response = requests.put(upload_href, data=content_bytes, timeout=30)
            upload_response.raise_for_status()
            logging.info(f"Файл '{file_name}' успешно загружен в папку '{folder_name}'.")

        except requests.RequestException as e:
            logging.error(f"Ошибка при загрузке файла: {e}")
            raise


def main():
    # Получение токена из переменных окружения (не хардкодить в коде!)
    # Перед запуском установите: export YANDEX_TOKEN='ваш_токен'
    yandex_token = os.getenv("YANDEX_TOKEN")
    if not yandex_token:
        logging.error("Не найден токен Яндекс.Диска. Установите переменную окружения YANDEX_TOKEN.")
        return

    # 1. Получение IP
    ip_client = IpifyClient()
    current_ip = ip_client.get_public_ip()
    logging.info(f"Текущий IP-адрес: {current_ip}")

    # 2. Получение геоинформации
    geo_client = IpInfoClient()
    geo_data = geo_client.get_geo_info(current_ip)
    logging.info(f"Получены геоданные: {geo_data}")

    # 3. Подготовка JSON данных в памяти
    json_bytes = json.dumps(geo_data, indent=4, ensure_ascii=False).encode('utf-8')
    file_name = f"ip_info_{current_ip}.json"
    folder_name = "IpDetector_Project"

    # 4. Загрузка на Яндекс.Диск
    disk_client = YandexDiskClient(yandex_token)
    disk_client.create_folder(folder_name)
    disk_client.upload_file_from_memory(folder_name, file_name, json_bytes)


if __name__ == "__main__":
    main()