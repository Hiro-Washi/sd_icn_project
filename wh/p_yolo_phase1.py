import cefpyco
import cv2
import time
import json
from ultralytics import YOLO

BASE_NAME_RAW = "ccnx:/factory/camera/raw"
BASE_NAME_YOLO = "ccnx:/factory/camera/yolo"

# フル量子化TFLiteモデルの読み込み
model_path = "/home/pi5/yolov8n_integer_quant.tflite"
model = YOLO(model_path)

# Ceforeのペイロード安全上限（約4KB未満に設定）
MAX_PAYLOAD_SIZE = 4000

def producer():
    cap = cv2.VideoCapture("/home/pi5/wh/sd_icn_project/video_edge/data/test_video_lab.mp4")

    with cefpyco.create_handle() as handle:
        handle.register(BASE_NAME_RAW)
        handle.register(BASE_NAME_YOLO)
        print("=== [Phase 1] Edge Node Started ===")
        print(f"Listening on: {BASE_NAME_RAW} and {BASE_NAME_YOLO}")
        print(f"Max Payload Limit: {MAX_PAYLOAD_SIZE} bytes")

        while True:
            try:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()

                # Interestの受信待ち
                interest = handle.receive(timeout_ms=10)

                if interest.is_interest:
                    start_process = time.perf_counter()

                    # ==========================================
                    # シナリオA: Raw画像（超高圧縮・1パケット）
                    # ==========================================
                    if interest.name.startswith(BASE_NAME_RAW):
                        # 限界まで解像度と品質を落とす
                        frame_resized = cv2.resize(frame, (160, 120))
                        _, encoded_img = cv2.imencode('.jpg', frame_resized, [cv2.IMWRITE_JPEG_QUALITY, 20])
                        payload = encoded_img.tobytes()

                        proc_time = (time.perf_counter() - start_process) * 1000

                        # 安全装置: 4KBを超えたら送信しない（Consumer側はタイムアウトになる）
                        if len(payload) > MAX_PAYLOAD_SIZE:
                            print(f"[RAW ] Blocked! Size {len(payload)} bytes exceeds limit.")
                            continue

                        print(f"[RAW ] Sent JPEG ({len(payload):>4} bytes) in {proc_time:.1f} ms")
                        handle.send_data(interest.name, payload, 0)

                    # ==========================================
                    # シナリオB: Semantic Edge（YOLO -> JSON）
                    # ==========================================
                    elif interest.name.startswith(BASE_NAME_YOLO):
                        results = model(frame, verbose=False)

                        detections = []
                        for box in results[0].boxes:
                            detections.append({
                                "cls": int(box.cls),
                                "conf": round(float(box.conf), 2),
                                "bbox": [int(x) for x in box.xyxy.tolist()[0]]
                            })

                        payload = json.dumps(detections).encode('utf-8')
                        proc_time = (time.perf_counter() - start_process) * 1000

                        if len(payload) > MAX_PAYLOAD_SIZE:
                            print(f"[YOLO] Blocked! Size {len(payload)} bytes exceeds limit.")
                            continue

                        print(f"[YOLO] Sent JSON ({len(payload):>4} bytes) in {proc_time:.1f} ms")
                        handle.send_data(interest.name, payload, 0)

            except KeyboardInterrupt:
                break
    cap.release()

if __name__ == "__main__":
    producer()
