from google import genai
from dotenv import load_dotenv
import os
import requests
from xml.etree import ElementTree as ET
import telegram
import asyncio


def get_arxiv_papers(url, search_query, sortBy, sortOrder, max_results):
    url = url
    params = {
        "search_query": search_query,
        "sortBy": sortBy,
        "sortOrder": sortOrder,
        "max_results": max_results
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Không thể kết nối tới arXiv API")
    
    return response

def get_content(response):
    root = ET.fromstring(response.content)
    papers = []

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            paper = {
                "title": entry.find("{http://www.w3.org/2005/Atom}title").text,
                "authors": [author.find("{http://www.w3.org/2005/Atom}name").text 
                            for author in entry.findall("{http://www.w3.org/2005/Atom}author")],
                "published": entry.find("{http://www.w3.org/2005/Atom}published").text,
                "abstract": entry.find("{http://www.w3.org/2005/Atom}summary").text,
                "pdf_link": entry.find("{http://www.w3.org/2005/Atom}link[@title='pdf']").get("href")
            }
            papers.append(paper)
    
    return papers

def summarize_abstract(papers):
    client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

    for paper in papers:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"""Hãy giải thích đoạn abstract của bài báo về khoa học máy tính này từ 5 tới 10 gạch đầu dòng, 
            trước khi giải thích hãy đưa ra một câu tóm tắt chung cho bài báo. Lưu ý câu trả lời không chứa markdown. 
            Đây là phần abstract của bài báo bạn cần tóm tắt: {paper['abstract']}"""
        )
        paper['summary'] = response.text
    
    return papers

async def send_to_telegram(papers):
    bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    for paper in papers:
        message = (
            f"📄 *Tiêu đề*: {paper['title']}\n"
            f"✍️ *Tác giả*: {', '.join(paper['authors'])}\n"
            f"📅 *Ngày xuất bản*: {paper['published']}\n"
            f"✂️ *Tóm tắt*: {paper['summary']}\n"
            f"📎 *Link PDF*: {paper['pdf_link']}"
            "\n\n"
        )
        await bot.send_message(chat_id=os.getenv('TELEGRAM_CHAT_ID'), text=message)
        

def main(url, search_query, sortBy, sortOrder, max_results):
    if not os.getenv('GITHUB_ACTIONS'):  # Chỉ load .env nếu không chạy trên GitHub
        load_dotenv()
    
    print("Đang lấy bài báo từ arXiv...")
    response = get_arxiv_papers(url, search_query, sortBy, sortOrder, max_results)
    papers = get_content(response)
    
    print("Đang tóm tắt abstracts...")
    papers = summarize_abstract(papers)
    
    print("Đang gửi qua Telegram...")
    import asyncio
    asyncio.run(send_to_telegram(papers))
    
    print("Hoàn tất!")
