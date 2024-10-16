import hashlib
import requests
import time

# URL вашего сервера
SERVER_URL = "http://127.0.0.1:8000/blockchain/mine"

# Функция для хэширования блока
def hash_block(index, timestamp, data, previous_hash, nonce):
    block_string = f"{index}{timestamp}{data}{previous_hash}{nonce}"
    return hashlib.sha256(block_string.encode()).hexdigest()

# Функция для майнинга блока
def mine_block(last_block, data, miner_address, difficulty):
    index = last_block['index'] + 1
    timestamp = time.time()
    previous_hash = last_block['hash']
    
    nonce = 0  # Начальное значение nonce
    prefix = '0' * difficulty  # Префикс, который должен быть в начале хэша
    
    # Счётчики для расчёта хэшрейта
    hash_count = 0
    start_time = time.time()
    
    print(f"Starting to mine block {index}...")

    while True:
        # Генерируем хэш блока
        block_hash = hash_block(index, timestamp, data, previous_hash, nonce)
        
        # Увеличиваем количество выполненных хэшей
        hash_count += 1

        # Проверяем, удовлетворяет ли хэш условиям сложности
        if block_hash.startswith(prefix):
            end_time = time.time()
            mining_duration = end_time - start_time
            hash_rate = hash_count / mining_duration  # Хэшрейт в H/s
            print(f"Block mined! Nonce: {nonce}, Hash: {block_hash}")
            print(f"Mining duration: {mining_duration:.2f} seconds")
            print(f"Hash rate: {hash_rate:.2f} H/s")
            
            # Отправляем блок на сервер
            send_mined_block(index, timestamp, data, previous_hash, nonce, block_hash, miner_address)
            break  # Если блок успешно отправлен, выходим из цикла

        # Если хэш не подходит, увеличиваем nonce и продолжаем
        nonce += 1
        
        # Каждые 10 000 хэшей выводим промежуточную информацию
        if hash_count % 10000 == 0:
            current_time = time.time()
            elapsed_time = current_time - start_time
            current_hash_rate = hash_count / elapsed_time
            print(f"Hash count: {hash_count}, Current hash rate: {current_hash_rate:.2f} H/s")

# Функция для отправки майнингового блока на сервер
def send_mined_block(index, timestamp, data, previous_hash, nonce, block_hash, miner_address):
    block_data = {
        "index": index,
        "timestamp": timestamp,
        "data": data,
        "previous_hash": previous_hash,
        "nonce": nonce,
        "hash": block_hash,
        "miner_address": miner_address
    }
    
    try:
        response = requests.post(SERVER_URL, json=block_data)
        if response.status_code == 200:
            print(f"Block successfully mined and added to the blockchain: {response.json()}")
        else:
            print(f"Failed to mine block. Status code: {response.status_code}, Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending block to server: {e}")

# Получение последнего блока (запрос к серверу)
def get_last_block():
    try:
        response = requests.get("http://127.0.0.1:8000/blockchain/last_block")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch last block. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching last block: {e}")
        return None

# Основная функция
def main():
    miner_address = "cc80f17b-0668-47b2-ad0a-69acba8f7f11"  # Укажите ваш адрес майнера
    data = "Some data to include in the block"
    difficulty = 2  # Укажите сложность (например, 4)

    while True:
        last_block = get_last_block()
        if last_block:
            mine_block(last_block, data, miner_address, difficulty)
        else:
            print("Could not fetch the last block. Retrying in 10 seconds...")
            time.sleep(10)  # Пауза перед повторной попыткой

if __name__ == "__main__":
    main()
