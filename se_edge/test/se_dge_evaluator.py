import cefpyco
import time
import sys

def fetch_data(handle, interest_name, description):
    """指定したInterestを送信し、Dataを受信してサイズと遅延を計測する"""
    print(f"\n--- 測定開始: {description} ---")
    print(f"Sending Interest: {interest_name}")
    
    start_time = time.time()
    handle.send_interest(interest_name, 0)

    # タイムアウト設定用
    timeout = 5.0 
    
    while True:
        try:
            # タイムアウト付きで受信待機
            data = handle.receive(timeout_ms=int(timeout * 1000))
            
            if data.is_data and data.name == interest_name:
                rtt = (time.time() - start_time) * 1000 # ミリ秒に変換
                payload_size = len(data.payload)
                
                print(f"[Success] Data received!")
                print(f"  - Payload Size : {payload_size} Bytes")
                print(f"  - RTT (Latency): {rtt:.2f} ms")
                return payload_size, rtt
                
            elif data.is_interest:
                pass # 他のInterestは無視
                
        except Exception as e:
            # 受信タイムアウトなどのエラー
            print(f"[Timeout/Error] Could not receive data for {interest_name}. ({e})")
            return None, None

def run_evaluation():
    # 測定用パラメータ
    RAW_INTEREST = "ccnx:/factory/lineA/camera/raw/chunk_1"
    SEM_INTEREST = "ccnx:/factory/lineA/camera/semantic/chunk_1"

    with cefpyco.create_handle() as handle:
        print("=========================================")
        print(" Phase A: Data Reduction Ratio Evaluation")
        print("=========================================")
        
        # 1. Baseline (Raw Video) の計測
        raw_size, raw_rtt = fetch_data(handle, RAW_INTEREST, "Baseline (Raw Video Push/Pull)")
        
        # 少し待機
        time.sleep(2)
        
        # 2. Proposed (Semantic JSON) の計測
        sem_size, sem_rtt = fetch_data(handle, SEM_INTEREST, "Proposed (Semantic Communication)")
        
        # 結果の比較と計算
        if raw_size and sem_size:
            reduction_ratio = ((raw_size - sem_size) / raw_size) * 100
            
            print("\n=========================================")
            print(" [評価結果 (Evaluation Results)]")
            print("=========================================")
            print(f" Baseline (Raw) Size : {raw_size} Bytes")
            print(f" Proposed (Sem) Size : {sem_size} Bytes")
            print(f" -> Data Reduction   : {reduction_ratio:.4f}% 削減!")
            print("-----------------------------------------")
            print(f" Baseline RTT        : {raw_rtt:.2f} ms")
            print(f" Proposed RTT        : {sem_rtt:.2f} ms")
            print("=========================================")

if __name__ == "__main__":
    run_evaluation()
