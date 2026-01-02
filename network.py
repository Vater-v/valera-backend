import socket
import threading
import json
import datetime
from session import GameSession
from handlers import PacketRouter

HOST = '0.0.0.0'
PORT = 5006

# Блокировка для записи в файл из разных потоков
log_lock = threading.Lock()

def log_to_jsonl(data: dict, ip: str, direction: str = "IN"):
    """Записывает событие в файл traffic.jsonl"""
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": ip,
        "direction": direction,
        "payload": data
    }

    with log_lock:
        with open("traffic.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

def extract_json(text: str):
    """Ищет JSON-объект внутри строки, игнорируя мусор по краям"""
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start : end + 1]
    return None

def handle_client(client_socket, address):
    ip, port = address
    print(f"[+] [{ip}:{port}] Подключен")

    session = GameSession(ip, port)
    router = PacketRouter()
    buffer = ""

    try:
        while True:
            data = client_socket.recv(4096)
            if not data:
                break

            # Декодируем с игнором ошибок (чтобы смайлики или бинарщина не ломали скрипт)
            try:
                chunk = data.decode('utf-8', errors='ignore')
                buffer += chunk

                # Используем разделитель из логов
                if "🎯" in buffer:
                    parts = buffer.split("🎯")
                    # Последний кусок оставляем в буфере (может быть неполным)
                    buffer = parts.pop()

                    for part in parts:
                        clean_part = part.strip()
                        if not clean_part: continue

                        json_str = extract_json(clean_part)
                        if json_str:
                            try:
                                json_data = json.loads(json_str)

                                # --- ЛОГИРОВАНИЕ ---
                                log_to_jsonl(json_data, ip, direction="IN")
                                # -------------------

                                router.process(json_data, session)
                            except json.JSONDecodeError:
                                pass # Битая строка, бывает
            except Exception as e:
                print(f"[ERR] Ошибка обработки буфера: {e}")

    except Exception as e:
        print(f"[!] Ошибка сокета: {e}")
    finally:
        client_socket.close()
        print(f"[-] [{ip}:{port}] Отключен.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[*] Сервер-анализатор запущен на {HOST}:{PORT}")
        while True:
            client, addr = server.accept()
            threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[*] Стоп")

if __name__ == '__main__':
    start_server()
