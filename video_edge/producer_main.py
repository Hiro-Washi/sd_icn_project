# video_edge/producer_main.py
import sys
import os
import json
import cv2
import cefpyco

# 上位ディレクトリのモジュールをインポートするためのパス追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.config import PREFIX_BASE, RAW_SUFFIX, SEM_SUFFIX
from common.cef_utils import chunk_data

VIDEO_PATH = "video_edge/data/test_video_lab.mp4"

def get_latest_frame_as_jpeg():
    """動画から1フレームを取得し、JPEGバイト列に変換する(ストリームの模倣)"""
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("[Error] 動画ファイルが開けません。パスを確認してください。")
        return b""
    
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        # 画質を少し落としてJPEGエンコード (例: 80%)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        result, encimg = cv2.imencode('.jpg', frame, encode_param)
        if result:
            return encimg.tobytes()
    return b""

def get_dummy_semantic_json():
    """YOLO推論結果を模したセマンティックデータを作成"""
    data = {
        "timestamp": 1716789000,
        "detections": [
            {"class": "person", "confidence": 0.95},
            {"class": "forklift", "confidence": 0.88}
        ],
        "anomaly": False
    }
    return json.dumps(data).encode('utf-8')

def producer():
    with cefpyco.create_handle() as handle:
        handle.register(PREFIX_BASE)
        print("=========================================")
        print(f" [Video Edge] Producer Started")
        print(f" Listening on: {PREFIX_BASE}")
        print("=========================================")

        while True:
            try:
                interest = handle.receive()
                if not interest.is_interest:
                    continue

                # --- Baseline: 生画像(JPEG)の要求 ---
                if RAW_SUFFIX in interest.name:
                    print(f"\n[Req] Raw Image chunk {interest.chunk_num} requested.")
                    # 初回(Chunk 0)要求時に画像をキャプチャしてチャンク分割
                    if interest.chunk_num == 0:
                        jpeg_bytes = get_latest_frame_as_jpeg()
                        # グローバル変数等にキャッシュするのが実用的ですが、
                        # 今回は単体テストとして都度生成・分割します
                        chunks = chunk_data(jpeg_bytes)
                        end_chunk_num = len(chunks) - 1
                    
                    # 該当チャンクを送信
                    if interest.chunk_num <= end_chunk_num:
                        payload = chunks[interest.chunk_num]
                        handle.send_data(
                            name=interest.name, 
                            payload=payload, 
                            chunk_num=interest.chunk_num, 
                            end_chunk_num=end_chunk_num
                        )
                        print(f"  -> Sent Raw Chunk {interest.chunk_num}/{end_chunk_num} ({len(payload)} bytes)")

                # --- Proposed: セマンティック(JSON)の要求 ---
                elif SEM_SUFFIX in interest.name:
                    print(f"\n[Req] Semantic JSON requested.")
                    json_bytes = get_dummy_semantic_json()
                    # JSONは小さいので1チャンク(Chunk 0)で完了
                    handle.send_data(
                        name=interest.name, 
                        payload=json_bytes, 
                        chunk_num=0, 
                        end_chunk_num=0
                    )
                    print(f"  -> Sent Semantic JSON ({len(json_bytes)} bytes)")

            except KeyboardInterrupt:
                print("\nShutting down.")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    producer()
