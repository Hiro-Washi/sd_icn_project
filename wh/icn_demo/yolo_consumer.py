# wh/icn_demo/yolo_consumer.py
import cefpyco
import time
import csv
import os
from datetime import datetime

# ==========================================
# 実験パラメータ設定
# ==========================================
#TARGET_NAME = "ccnx:/factory/camera/raw" # シナリオA（画像ストリーム）
TARGET_NAME = "ccnx:/factory/camera/yolo"  # シナリオB（Semantic Edge）

NUM_REQUESTS = 100       # 実験の総サンプル数（要求回数）
INTERVAL_SEC = 0.2       # Interestの送信間隔（0.2秒 = 5回/秒）
TIMEOUT_MS = 2000        # タイムアウト時間（ミリ秒）
# ==========================================

def consumer():
    # CSVファイル名の生成 (例: result_raw_20260522_150000.csv)
    scenario_name = TARGET_NAME.split('/')[-1]
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"result_{scenario_name}_{timestamp_str}.csv"

    rtt_list = []
    size_list = []

    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        # CSVのヘッダー（1行目）
        writer.writerow(["Sequence", "Timestamp", "Status", "RTT_ms", "Payload_bytes", "Payload_Data"])

        with cefpyco.create_handle() as handle:
            print(f"=== 実験開始: {TARGET_NAME} ===")
            print(f"サンプル数: {NUM_REQUESTS} 回 / 送信間隔: {INTERVAL_SEC} 秒")
            print(f"保存先CSV : {csv_filename}\n")

            for i in range(NUM_REQUESTS):
                seq = i + 1
                send_time = time.perf_counter()
                unix_time = time.time()

                # SMI (Symbolic Interest) の送信
                handle.send_symbolic_interest(TARGET_NAME)

                # データの待ち受け
                data = handle.receive(timeout_ms=TIMEOUT_MS)

                if data.is_data and data.name == TARGET_NAME:
                    rtt = (time.perf_counter() - send_time) * 1000
                    payload_len = len(data.payload)

                    # 受信したバイトデータを文字列（JSON）にデコード
                    try:
                        payload_str = data.payload.decode('utf-8')
                    except Exception as e:
                        payload_str = "[Decode Error]"

                    # 成功したデータをリストとCSVに記録
                    rtt_list.append(rtt)
                    size_list.append(payload_len)
                    writer.writerow([seq, unix_time, "Success", round(rtt, 2), payload_len, payload_str])

                    print(f"[{seq:03d}/{NUM_REQUESTS}] 成功 | {payload_len} bytes | RTT: {rtt:.2f} ms")
                    # コンソールでも中身をチラ見せ
                    print(f"      -> {payload_str[:80]}...")
                else:
                    # タイムアウトまたはパケットロス
                    writer.writerow([seq, unix_time, "Timeout/Loss", "", ""])
                    print(f"[{seq:03d}/{NUM_REQUESTS}] タイムアウト")

                # 指定した送信間隔（INTERVAL_SEC）を厳密に守るための待機計算
                elapsed = time.perf_counter() - send_time
                sleep_time = max(0.0, INTERVAL_SEC - elapsed)
                time.sleep(sleep_time)

    # 実験サマリの表示
    print("\n=== 実験完了 ===")
    if rtt_list:
        avg_rtt = sum(rtt_list) / len(rtt_list)
        avg_size = sum(size_list) / len(size_list)
        success_rate = (len(rtt_list) / NUM_REQUESTS) * 100

        print(f"取得成功率: {success_rate:.1f} % ({len(rtt_list)}/{NUM_REQUESTS})")
        print(f"平均サイズ: {avg_size:.1f} bytes")
        print(f"平均 RTT  : {avg_rtt:.2f} ms")
        print(f"詳細データは {csv_filename} に保存されました。")

if __name__ == "__main__":
    consumer()
