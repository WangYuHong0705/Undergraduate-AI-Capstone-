import requests
from bs4 import BeautifulSoup
import time
import json
import re
print(123)
def clean_text(text):
    """
    1. 移除 PTT 簽名檔 (通常在 -- 之後)
    2. 移除 ASCII 藝術與特殊符號 (只保留中英文、數字與基本標點)
    """
    if not text:
        return ""
    
    # 移除簽名檔 (由 -- 開始到結尾)
    text = text.split('--')[0]
    
    # 移除網址
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # 只保留中文 (\u4e00-\u9fa5)、英文 (a-zA-Z)、數字 (0-9) 
    # 以及常用標點符號 (，。！？：；「」『』()（）)
    clean_pattern = re.compile(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？：；「」『』()（）\n\s]')
    text = clean_pattern.sub('', text)
    
    # 移除過多的換行，讓資料更緊湊
    text = re.sub(r'\n+', '\n', text).strip()
    return text

def extract_classification(title):
    """從標題中提取 [分類] 內容"""
    match = re.search(r'\[(.*?)\]', title)
    return match.group(1) if match else ""

def fetch_post_details(url):
    try:
        res = requests.get(url, cookies={'over18': '1'}, timeout=10)
        if res.status_code != 200: return None
        
        soup = BeautifulSoup(res.text, 'html.parser')
        main_content = soup.find(id='main-content')
        if not main_content: return None

        # 1. 取得作者
        author = ""
        meta_author = main_content.find('span', class_='article-meta-tag', string='作者')
        if meta_author:
            author = meta_author.find_next_sibling('span').text.strip()

        # 2. 統計總留言數 (所有推、噓、箭頭)
        number_of_comments = len(main_content.find_all(class_='push'))

        # 3. 內文清洗 (在移除 tag 前先抓文字)
        # 先暫存原始文字，後續進行切割與過濾
        raw_text = main_content.get_text()
        # 由於 get_text 會包含元數據，我們精確一點，只取文章主體
        # 移除元數據區塊
        for meta in main_content.find_all(class_='article-metaline'): meta.decompose()
        for meta in main_content.find_all(class_='article-metaline-right'): meta.decompose()
        for push in main_content.find_all(class_='push'): push.decompose()
        
        content = clean_text(main_content.get_text())

        return {
            "author": author,
            "content": content,
            "number_of_comments": number_of_comments
        }
    except Exception as e:
        print(f"   ❌ 內頁錯誤: {e}")
        return None
def convert_push_to_int(push_str):
    if not push_str:
        return 0
    push_str = push_str.strip()
    
    if push_str == '爆':
        return 150  # 或你可以設 200，看你定義
    
    if push_str.startswith('X'):
        try:
            return -int(push_str[1:])
        except:
            return -1
    
    try:
        return int(push_str)
    except:
        return 0
def crawl_ptt_v2(board, start_page, end_page, output_file="web_crawl_data_real.json"):
    all_posts = []
    for page in range(start_page, end_page + 1):
        url = f"https://www.ptt.cc/bbs/{board}/index{page}.html"
        print(f"🌐 正在爬取 {board} 版 第 {page} 頁...")
        
        try:
            res = requests.get(url, cookies={'over18': '1'})
            soup = BeautifulSoup(res.text, 'html.parser')
            for entry in soup.find_all(class_='r-ent'):
                title_tag = entry.find(class_='title').a
                if not title_tag: continue
                
                title = title_tag.text.strip()
                classification = extract_classification(title) # 提取分類
                title = re.sub(r'\[.*?\]', '', title).strip()
                link = "https://www.ptt.cc" + title_tag['href']
                
                nrec = entry.find(class_='nrec').text.strip()
                #push_label = nrec if nrec else "0"
                push_label = convert_push_to_int(nrec)
                print(push_label)
                is_popular = (nrec == '爆')

                print(f"   📖 處理: {title[:15]}...")
                details = fetch_post_details(link)
                
                if details:
                    all_posts.append({
                        "title": title,
                        "classification": classification, # 這裡現在會有內容了，例如 "問卦"
                        "author": details["author"],
                        "content": details["content"], # 這裡的 ASCII 藝術會被清除
                        "push": push_label,
                        "number_of_comments": details["number_of_comments"],
                        "popular": is_popular
                    })
                time.sleep(0.5)
        except Exception as e:
            print(f"❌ 錯誤: {e}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=4)
    print(f"\n✅ 完成！資料存至 {output_file}")

if __name__ == "__main__":
    crawl_ptt_v2("Gossiping", 1, 50)