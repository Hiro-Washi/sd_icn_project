import cefpyco
import time

def consumer():
    # ユーザーからの自然言語要求 (NLI)
    user_query = "is there any fire on line A"
    
    # 空白をアンダースコアに変換してICNの名前に組み込む
    # 例: ccnx:/factory/ask/is_there_any_fire_on_line_A
    formatted_query = user_query.replace(" ", "_")
    interest_name = f"ccnx:/factory/ask/{formatted_query}"
    
    with cefpyco.create_handle() as handle:
        print(f"Sending NLI Interest: {interest_name}")
        handle.send_interest(interest_name, 0)

        start_time = time.time()
        while True:
            try:
                data = handle.receive()
                # Interest名に合致するDataパケットを受信した場合
                if data.is_data and data.name == interest_name:
                    rtt = time.time() - start_time
                    
                    # LLMのテキスト結果をバイト列からデコードして変数に格納
                    result_text = data.payload.decode('utf-8')
                    
                    print("\n=== Received Response from Semantic Engine ===")
                    print(f"Round Trip Time (RTT): {rtt:.4f} seconds")
                    print(f"Result Data:\n{result_text}")
                    print("==============================================")
                    break
                    
            except KeyboardInterrupt:
                print("\nConsumer shutting down.")
                break

if __name__ == "__main__":
    consumer()
