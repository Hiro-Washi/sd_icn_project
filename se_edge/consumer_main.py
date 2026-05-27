# se_edge/consumer_main.py
import sys
import os
import time
import cefpyco

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import PREFIX_BASE, RAW_SUFFIX, SEM_SUFFIX

def fetch_data_completely(handle, base_name, description):
    """Chunk 0からEnd Chunkまで全て取得し、サイズとRTTを計測する"""
    print(f"\n--- 測定開始: {description} ---")
    
    total_bytes = 0
    start_time = time.time()
    
    # まずChunk 0を要求
    handle.send_interest(base_name, chunk_num=0)
    
    expected_chunk = 0
    end_chunk = None

    while True:
        try:
            # タイムアウト設定 (2秒)
            data = handle.receive(timeout_ms=2000)
            
            if data.is_data and data.name == base_name and data.chunk_num == expected_chunk:
                total_bytes += len(data.payload)
                
                # 初回受信時にエンドチャンク番号を把握
                if end_chunk is None:
                    end_chunk = data.end_chunk_num
                
                print(f"  [Recv] Chunk {data.chunk_num}/{end_chunk} ({len(data.payload)} bytes)")
                
                # 全チャンク受信完了か判定
                if expected_chunk == end_chunk:
                    rtt = (time.time() - start_time) * 1000
                    print(f"  -> [Success] 全データ受信完了 (Total: {total_bytes} bytes, RTT: {rtt:.2f} ms)")
                    return total_bytes, rtt
                
                # 次のチャンクを要求
                expected_chunk += 1
                handle.send_interest(base_name, chunk_num=expected_chunk)

        except Exception as e:
            print(f"  -> [Timeout/Error] データ取得失敗: {e}")
            return None, None

def run_evaluation():
    raw_name = f"{PREFIX_BASE}/{RAW_SUFFIX}"
    sem_name = f"{PREFIX_BASE}/{SEM_SUFFIX}"

    with cefpyco.create_handle() as handle:
        print("=========================================")
        print(" Phase A: Communication Efficiency Eval")
        print("=========================================")
        
        # 1. Baseline (Raw JPEG Stream)
        raw_size, raw_rtt = fetch_data_completely(handle, raw_name, "Baseline (Raw JPEG Frame)")
        
        time.sleep(2)
        
        # 2. Proposed (Semantic JSON)
        sem_size, sem_rtt = fetch_data_completely(handle, sem_name, "Proposed (Semantic JSON)")
        
        # 評価結果出力
        if raw_size and sem_size:
            reduction_ratio = ((raw_size - sem_size) / raw_size) * 100
            print("\n=========================================")
            print(" [評価結果サマリー]")
            print("=========================================")
            print(f" Baseline 通信量 : {raw_size} Bytes")
            print(f" Proposed 通信量 : {sem_size} Bytes")
            print(f" 削減率 (Reduction): {reduction_ratio:.4f} %")
            print("-----------------------------------------")
            print(f" Baseline RTT    : {raw_rtt:.2f} ms")
            print(f" Proposed RTT    : {sem_rtt:.2f} ms")
            print("=========================================")

if __name__ == "__main__":
    run_evaluation()
