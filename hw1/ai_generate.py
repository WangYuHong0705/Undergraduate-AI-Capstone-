import json
import time
import google.generativeai as genai
import pandas as pd

# ==========================================
# 1. 配置與初始化
# ==========================================
genai.configure(api_key="api_key")  # ⚠️ 建議不要寫死 key

model = genai.GenerativeModel('gemma-3-27b-it')

# ==========================================
# 2. snippet 處理
# ==========================================
def extract_snippet(text):
    if not text:
        return ""
    
    first_line = text.split("\n")[0]
    return first_line[:20]

# ==========================================
# 3. AI 生成函數（依原文長度生成）
# ==========================================
def generate_ptt_content(title, board, snippets, original_text):
    # 計算原文長度（中文+英文字數）
    original_len = len(original_text)
    
    prompt = f"""
你現在是一個發文者。請根據以下資訊，以真人撰寫文章的角度撰寫一篇發文內容。

【標題】：{title}
【看板】：{board}
【參考內容提示】：{snippets}

請注意：
1. 語氣要像參考內容。
2. 不要太客氣，也不要像 AI 的罐頭回覆。
3. 文章長度大約 {original_len} 字，長度盡量接近原文。
4. 直接輸出內文，不要附上標題、看板等內容。
5. 可以根據標題自由發揮文章內容。
"""
    try:
        #print(prompt)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error generating for {title}: {e}")
        return None

# ==========================================
# 4. 讀取資料
# ==========================================
with open("web_crawl_data_real.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

ai_data = []

print(f"開始生成 AI 文章，總計 {len(raw_data)} 筆...")

# ==========================================
# 5. 主迴圈
# ==========================================
count = 0
for i, item in enumerate(raw_data):
    print(f"進度：{i+1}/{len(raw_data)}")
    count += 1
    if (count > 100):
      break
    snippet = extract_snippet(item.get('content', ''))
    original_text = item.get('content', '')
    
    ai_content = generate_ptt_content(
        item.get('title', ''),
        item.get('classification', ''),
        snippet,
        original_text
    )
    
    if ai_content:
        ai_entry = {
            "title": item.get('title', ''),
            "classification": item.get('classification', ''),
            "author": "AI_Assistant",
            "content": ai_content,
            "label": 1
        }
        ai_data.append(ai_entry)
    
    # API 限制（Free Tier）
    time.sleep(1.5)
    
    

# ==========================================
# 6. 儲存結果
# ==========================================
with open("ai_generated_data2.json", "w", encoding="utf-8") as f:
    json.dump(ai_data, f, ensure_ascii=False, indent=4)

print("✅ AI 數據生成完畢！") 
