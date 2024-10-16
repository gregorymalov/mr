from core.settings import db_settings as db
from fastapi import APIRouter, HTTPException
import hashlib
import time
import uuid
from pydantic import BaseModel
from jose import jwt


# Константы
BLOCK_REWARD = 1  # Награда за блок
DIFFICULTY = 2    # Сложность майнинга (количество нулей в начале хэша)

# Инициализация FastAPI
router = APIRouter()

# # Подключение к MongoDB
# client = AsyncIOMotorClient('mongodb://localhost:27017')
# db = client.blockchain

# Функции
def generate_uuid():
    return str(uuid.uuid4())

def hash_block(index, timestamp, data, previous_hash, nonce):
    block_string = f"{index}{timestamp}{data}{previous_hash}{nonce}"
    return hashlib.sha256(block_string.encode()).hexdigest()

# Проверка правильности блока
def is_valid_block(block, difficulty):
    prefix = '0' * difficulty
    block_hash = hash_block(block['index'], block['timestamp'], block['data'], block['previous_hash'], block['nonce'])
    return block_hash.startswith(prefix)

# Модель для данных майнинга
class MiningData(BaseModel):
    data: str
    miner_address: str
    nonce: int

# Маршрут для майнинга нового блока
@router.post("/mine")
async def mine_block(data: MiningData):
    # Получаем последний блок
    last_block = await db.blocks.find_one(sort=[("index", -1)])
    if not last_block:
        raise HTTPException(status_code=400, detail="No blocks found")

    # Создаем новый блок
    new_block = {
        '_id': generate_uuid(),
        'index': last_block['index'] + 1,
        'timestamp': time.time(),
        'data': data.data,
        'previous_hash': last_block['hash'],
        'nonce': data.nonce
    }

    # Проверяем, что хэш блока соответствует сложности
    if is_valid_block(new_block, DIFFICULTY):
        # Обновляем хэш блока
        new_block['hash'] = hash_block(new_block['index'], new_block['timestamp'], new_block['data'], new_block['previous_hash'], new_block['nonce'])

        # Награда майнеру
        miner = await db.machines.find_one({"address": data.miner_address})
        if miner:
            await db.machines.update_one({"address": data.miner_address}, {"$inc": {"balance": BLOCK_REWARD}})
            miner['balance'] += BLOCK_REWARD
            miner['transaction_history'].append({
                "type": "mining",
                "amount": BLOCK_REWARD,
                "timestamp": time.time()
            })
            await db.machines.update_one({"address": data.miner_address}, {"$set": {"transaction_history": miner['transaction_history']}})

        # Добавляем блок в базу данных
        await db.blocks.insert_one(new_block)
        return new_block
    else:
        raise HTTPException(status_code=400, detail="Invalid block. Hash does not meet the difficulty requirement.")

# Маршрут для получения последнего блока
@router.get("/last_block")
async def get_last_block():
    last_block = await db.blocks.find_one(sort=[("index", -1)])
    if not last_block:
        raise HTTPException(status_code=404, detail="No blocks found")
    return last_block

# Инициализация блокчейна (создание генезис-блока)
async def initialize_blockchain():
    existing_block = await db.blocks.find_one({"index": 0})
    if not existing_block:
        await create_genesis_block()

async def create_genesis_block():
    genesis_block = {
        "_id": generate_uuid(),
        "index": 0,
        "timestamp": time.time(),
        "transactions": [],
        "previous_hash": "0",
        "nonce": 0,
        "hash": ""
    }
    genesis_block["hash"] = hash_block(genesis_block['index'], genesis_block['timestamp'], genesis_block['transactions'], genesis_block['previous_hash'], genesis_block['nonce'])
    await db.blocks.insert_one(genesis_block)
    print("Genesis block created")

# # Отправка коина
# @router.post("/transaction")
# async def send_transaction(transaction: Transaction):
#     sender = await db.machines.find_one({"address": transaction.sender})
#     recipient = await db.machines.find_one({"address": transaction.recipient})

#     if not sender or not recipient:
#         raise HTTPException(status_code=404, detail="Sender or recipient not found")
#     if sender['balance'] < transaction.amount:
#         raise HTTPException(status_code=400, detail="Insufficient funds")

#     # Обновление балансов
#     await db.machines.update_one({"address": transaction.sender}, {"$inc": {"balance": -transaction.amount}})
#     await db.machines.update_one({"address": transaction.recipient}, {"$inc": {"balance": transaction.amount}})

#     # Обновление истории транзакций
#     sender['transaction_history'].append({
#         "type": "send",
#         "recipient": transaction.recipient,
#         "amount": transaction.amount,
#         "timestamp": time.time()
#     })
#     recipient['transaction_history'].append({
#         "type": "receive",
#         "sender": transaction.sender,
#         "amount": transaction.amount,
#         "timestamp": time.time()
#     })

#     await db.machines.update_one({"address": transaction.sender}, {"$set": {"transaction_history": sender['transaction_history']}})
#     await db.machines.update_one({"address": transaction.recipient}, {"$set": {"transaction_history": recipient['transaction_history']}})

#     return {"message": "Transaction completed"}

# # Получение всех блоков
# @router.get("/chain")
# async def get_chain():
#     blocks = await db.blocks.find().to_list(100)
#     return blocks

# @router.get("/height")
# async def get_chain_height():
#     last_block = await db.blocks.find_one(sort=[("index", -1)])
#     if not last_block:
#         raise HTTPException(status_code=404, detail="No blocks found")
#     return {"height": last_block["index"]}