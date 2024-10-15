from core.settings import db_settings as db
from fastapi import APIRouter, HTTPException
import hashlib
import time
import uuid
from pydantic import BaseModel
from jose import jwt

router = APIRouter()

# Константы
BLOCK_REWARD = 1  # Награда за блок

# Генерация UUID в качестве ID
def generate_uuid():
    return str(uuid.uuid4())

def calculate_hash(block):
    block_string = f"{block['_id']}{block['index']}{block['timestamp']}{block['previous_hash']}{block['transactions']}{block['nonce']}"
    return hashlib.sha256(block_string.encode()).hexdigest()

async def create_genesis_block():
    # Создание Genesis блока
    genesis_block = {
        "_id": generate_uuid(),  # Уникальный ID блока на основе UUID
        "index": 0,  # Это Genesis блок
        "timestamp": time.time(),
        "transactions": [],  # Нет транзакций
        "previous_hash": "0",  # Нет предыдущего блока
        "nonce": 0
    }
    genesis_block["hash"] = calculate_hash(genesis_block)  # Вычисляем хэш блока
    await db.blocks.insert_one(genesis_block)
    print("Genesis block created")

async def initialize_blockchain():
    # Проверка на наличие блоков
    existing_block = await db.blocks.find_one({"index": 0})
    if not existing_block:
        await create_genesis_block()
    else:
        print("Genesis block already exists")

# Модель для отправки транзакций
class Transaction(BaseModel):
    sender: str
    recipient: str
    amount: float

# Генерация ключей (адресов и ключей пользователя)
def generate_keys():
    public_key = generate_uuid()  # Псевдо-генерация адреса
    private_key = jwt.encode({"key": public_key}, "secret", algorithm="HS256")
    return public_key, private_key

# Хэширование блока
def hash_block(block):
    block_string = f"{block['index']}{block['timestamp']}{block['data']}{block['previous_hash']}{block['nonce']}"
    return hashlib.sha256(block_string.encode()).hexdigest()

# Майнинг блока
def mine_block(block, difficulty=4):
    block['nonce'] = 0
    prefix = '0' * difficulty
    while not hash_block(block).startswith(prefix):
        block['nonce'] += 1
    return hash_block(block)

# Создание нового пользователя
@router.post("/machines/create")
async def create_machine():
    public_key, private_key = generate_keys()
    user_id = generate_uuid()
    new_machine = {
        "_id": user_id,  # UUID как строка
        "address": public_key,
        "private_key": private_key,
        "balance": 0,
        "transaction_history": []
    }
    await db.machines.insert_one(new_machine)
    return new_machine

# Получение информации о пользователе
@router.get("/machines/{address}")
async def get_machine(address: str):
    machine = await db.machines.find_one({"address": address})
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine

# Майнинг нового блока
@router.post("/mine")
async def mine(data: str, miner_address: str):
    last_block = await db.blocks.find_one(sort=[("index", -1)])
    if not last_block:
        raise HTTPException(status_code=400, detail="No blocks found")

    new_block = {
        '_id': generate_uuid(),  # UUID как строка
        'index': last_block['index'] + 1,
        'timestamp': time.time(),
        'data': data,
        'previous_hash': last_block['hash'],
        'nonce': 0
    }
    new_block['hash'] = mine_block(new_block)

    # Награда майнеру
    miner = await db.machines.find_one({"address": miner_address})
    if miner:
        await db.machines.update_one({"address": miner_address}, {"$inc": {"balance": BLOCK_REWARD}})
        miner['balance'] += BLOCK_REWARD
        miner['transaction_history'].append({
            "type": "mining",
            "amount": BLOCK_REWARD,
            "timestamp": time.time()
        })
        await db.machines.update_one({"address": miner_address}, {"$set": {"transaction_history": miner['transaction_history']}})

    await db.blocks.insert_one(new_block)
    return new_block

# Отправка коина
@router.post("/transaction")
async def send_transaction(transaction: Transaction):
    sender = await db.machines.find_one({"address": transaction.sender})
    recipient = await db.machines.find_one({"address": transaction.recipient})

    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Sender or recipient not found")
    if sender['balance'] < transaction.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Обновление балансов
    await db.machines.update_one({"address": transaction.sender}, {"$inc": {"balance": -transaction.amount}})
    await db.machines.update_one({"address": transaction.recipient}, {"$inc": {"balance": transaction.amount}})

    # Обновление истории транзакций
    sender['transaction_history'].append({
        "type": "send",
        "recipient": transaction.recipient,
        "amount": transaction.amount,
        "timestamp": time.time()
    })
    recipient['transaction_history'].append({
        "type": "receive",
        "sender": transaction.sender,
        "amount": transaction.amount,
        "timestamp": time.time()
    })

    await db.machines.update_one({"address": transaction.sender}, {"$set": {"transaction_history": sender['transaction_history']}})
    await db.machines.update_one({"address": transaction.recipient}, {"$set": {"transaction_history": recipient['transaction_history']}})

    return {"message": "Transaction completed"}

# Получение всех блоков
@router.get("/chain")
async def get_chain():
    blocks = await db.blocks.find().to_list(100)
    return blocks

@router.get("/chain")
async def get_chain():
    blocks = await db.blocks.find().to_list(100)
    # Преобразуем блоки, чтобы избежать ObjectId
    return [{"id": block["id"], "index": block["index"], "timestamp": block["timestamp"],
             "data": block["data"], "previous_hash": block["previous_hash"], "hash": block["hash"],
             "nonce": block["nonce"]} for block in blocks]

@router.get("/height")
async def get_chain_height():
    last_block = await db.blocks.find_one(sort=[("index", -1)])
    if not last_block:
        raise HTTPException(status_code=404, detail="No blocks found")
    return {"height": last_block["index"]}