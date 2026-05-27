# common/cef_utils.py
from common.config import CHUNK_SIZE

def chunk_data(data_bytes):
    """バイナリデータをCHUNK_SIZEごとに分割し、リストで返す"""
    chunks = []
    for i in range(0, len(data_bytes), CHUNK_SIZE):
        chunks.append(data_bytes[i:i + CHUNK_SIZE])
    return chunks
