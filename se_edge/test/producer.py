import cefpyco
import ollama

BASE_NAME = "ccnx:/factory/ask"
OLLAMA_MODEL = "gemma3:1b" #"qwen3:latest" # 環境に合わせて変更してください

def analyze_with_llm(query_text):
    """LLMにクエリを投げて結果を変数で返す関数"""
    print(f"  [LLM] Analyzing query: '{query_text}'...")
    
    # システムプロンプト（LLMに役割と制約を与える）
    prompt = f"あなたはスマート工場の監視AIです。以下の管理者の質問に対して、推測される状況を簡潔に回答してください。\n質問: {query_text}"
    
    try:
        response = ollama.generate(model=OLLAMA_MODEL, prompt=prompt)
        return response['response']
    except Exception as e:
        print(f"  [LLM Error] {e}")
        return "エラー：LLMでの分析に失敗しました。"

def producer():
    with cefpyco.create_handle() as handle:
        handle.register(BASE_NAME)
        print("=========================================")
        print(" Semantic Engine Edge Started")
        print(f" Listening for Interests on: {BASE_NAME}")
        print("=========================================")
        
        while True:
            try:
                interest = handle.receive()
                
                if interest.is_interest:
                    print(f"\n[Cefore] Received Interest: {interest.name}")
                    
                    # Interest名からクエリ部分を抽出 (例: ccnx:/factory/ask/query_text)
                    name_parts = interest.name.split("/")
                    
                    if len(name_parts) > 3:
                        # 最後の要素（NLI部分）を取得し、アンダースコアを空白に戻す
                        raw_query = name_parts[-1]
                        query_text = raw_query.replace("_", " ")
                        
                        # セマンティックエンジン（Ollama）で分析し、結果を変数に格納
                        llm_result_text = analyze_with_llm(query_text)
                        
                        # テキストデータをバイト列にエンコードしてDataパケットで返信
                        response_data = llm_result_text.encode('utf-8')
                        handle.send_data(interest.name, response_data, 0)
                        
                        print(f"[Cefore] Sent Data packet (LLM Response, {len(response_data)} bytes)")
                    else:
                        print("[Cefore] Invalid Interest format. Ignored.")
                        
            except KeyboardInterrupt:
                print("\nProducer shutting down.")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    producer()
