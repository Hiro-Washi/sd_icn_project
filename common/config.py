# common/config.py

# ICN名前空間のベース
PREFIX_BASE = "ccnx:/factory/lineA/camera"
RAW_SUFFIX = "raw"
SEM_SUFFIX = "semantic"

# CeforeのパケットMTUを考慮した安全なチャンクサイズ (バイト)
# ※大きすぎるとSegmentation faultになるため約4KBに設定
CHUNK_SIZE = 4000
