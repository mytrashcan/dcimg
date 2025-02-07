import discord
import asyncio
import requests
from bs4 import BeautifulSoup
from discord.ext import commands
import os
from os.path import getsize
import hashlib
import logging
from telegram import Bot
from telegram import InputFile

# 디스코드 봇 Token 과 채널 ID
TOKEN = 'discordbot_token'
CHANNEL_IDS = ['channelid_1', 'channelid_2']  # 여러 채널 ID를 리스트로 설정 dcimgtest

# 텔레그램 봇 Token과 채팅 ID
TELEGRAM_BOT_TOKEN = 'telegrambot_token'
TELEGRAM_CHAT_ID = 'chat_id'

# 텔레그램 봇 초기화
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# 헤더 설정
headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "sec-ch-ua-mobile": "?0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ko-KR,ko;q=0.9"
}

# 중복된 제목을 저장할 set
sent_titles = set()
sent_image_links = set()

# 이미지 포함 여부 체크 함수
def image_check(text):
    return "icon_pic" in str(text)

# 크롤링 시작지점 위치 찾기
def finder(BASE_URL):
    startpoint = 0
    res = requests.get(BASE_URL, headers=headers)
    html = res.text
    soup = BeautifulSoup(html, 'html.parser')

    if "mgallery" in BASE_URL or "mini" in BASE_URL:
        pointer = soup.select("td.gall_subject")
    else:
        pointer = soup.select("td.gall_num")

    for item in pointer:
        if "공지" in item.text or "설문" in item.text or "고정" in item.text:
            startpoint += 1
    
    return startpoint

def image_download(BASE_URL):
    try:
        res = requests.get(BASE_URL, headers=headers)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')

        # 이미지 다운로드 받는 곳에서 시작
        image_download_contents = soup.select("div.appending_file_box ul li")
        for li in image_download_contents:
            img_tag = li.find('a', href=True)
            img_url = img_tag['href']

            file_ext = img_url.split('.')[-1]
            # 저장될 파일명
            savename = img_url.split("no=")[2]
            headers['Referer'] = BASE_URL
            response = requests.get(img_url, headers=headers)

            path = f"Image/{savename}"
            file_size = len(response.content)

            # 이미지 폴더가 없으면 생성
            if not os.path.exists("Image"):
                os.makedirs("Image")

            if os.path.isfile(path): # 이름이 똑같은 파일이 있으면
                if getsize(path) != file_size: # 파일 크기가 다를 경우
                    print("이름은 겹치는 다른 파일입니다. 다운로드 합니다.")
                    file = open(path + "[1]", "wb") # 경로 끝에 [1]을 추가해 받는다.
                    file.write(response.content)
                    file.close()
                else:
                    print("동일한 파일이 존재합니다. PASS")
                    return None
            else:
                file = open(path , "wb")
                file.write(response.content)
                file.close()

            return path  # 이미지 파일의 로컬 경로를 반환

    except Exception as e:
        logging.error(f"Error downloading image: {e}")
        return None

# 파일의 해시값을 계산하는 함수 (SHA256)
def calculate_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # 4K씩 읽어오면서 해시값 계산
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()  # SHA256 해시값 반환

# 텔레그램으로 이미지 보내기 (비동기 처리)
async def send_to_telegram(image_path, file_hash):
    try:
        with open(image_path, 'rb') as img_file:
            # 텔레그램으로 이미지 전송
            await telegram_bot.send_photo(chat_id=TELEGRAM_CHAT_ID, 
                                          photo=img_file)
                                          #, caption=f"hash: {file_hash}")
    except Exception as e:
        logging.error(f"Error sending image to Telegram: {e}")

# MyClient 클래스에서 이미지 처리 부분 수정
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = ""  # 클래스 인스턴스 변수로 text 초기화

    async def on_ready(self):
        print(f'We have logged in as {self.user}')
        
        # 여러 채널 ID를 리스트로 설정
        channel_ids = CHANNEL_IDS  # 여러 채널 ID를 리스트로 설정

        # 반복적으로 크롤링 작업을 수행하는 코드를 추가
        while True:
            BASE_URL = "https://gall.dcinside.com/mgallery/board/lists/?id=kizunaai"
            res = requests.get(BASE_URL, headers=headers)
            if res.status_code == 200:
                html = res.text
                soup = BeautifulSoup(html, 'html.parser')
                startpoint = int(finder(BASE_URL))
                doc = soup.select("td.gall_tit > a:nth-child(1)")
                for i in range(startpoint, len(doc)):  # 공지사항 거르고 시작 (인덱스 뒤부터)
                    link = "https://gall.dcinside.com" + doc[i].get("href")  # 글 링크
                    title = doc[i].text.strip()  # 제목
                    image_insert = image_check(doc[i])  # 이미지 포함 여부 True/False
                    print(link, title, image_insert)

                    # 이미 같은 제목을 보냈다면 건너뛰기
                    if title in sent_titles:
                        continue

                    if image_insert:  # 이미지 포함 시
                        img_path = image_download(link)  # 이미지 다운로드 후 파일 경로 받기
                        if img_path:  # 이미지가 제대로 다운로드된 경우
                            file_hash = calculate_file_hash(img_path)  # 파일 해시값 계산

                            # 각 채널에 이미지 전송
                            for channel_id in channel_ids:
                                channel = self.get_channel(int(channel_id))
                                if channel:
                                    await self.send_embed_image(channel, title, img_path, file_hash)  # 임베드 형식으로 이미지 전송
                                    sent_titles.add(title)  # 이미 보낸 제목 저장
                                    sent_image_links.add(link)  # 이미지 링크 저장

                            # 텔레그램으로 이미지 전송
                            await send_to_telegram(img_path, file_hash)

                    break  # 바로 break해서 첫 글만 가져옴

            # 10초마다 반복 실행
            await asyncio.sleep(7)  # 10초 대기 후 반복

    async def send_embed_image(self, channel, title, img_path, file_hash):
        """임베드 방식으로 이미지를 디스코드 채널로 전송하는 함수"""
        try:
            embed = discord.Embed(
                title=title,  # 글 제목
                #description=f"hash: {file_hash}",  # 해시값을 description에 포함
                color=0xFF5733  # 색상
            )
            embed.set_image(url=f"attachment://{os.path.basename(img_path)}")  # 첨부한 이미지로 임베드 설정

            with open(img_path, 'rb') as f:
                await channel.send(file=discord.File(f, filename=os.path.basename(img_path)), embed=embed)
        except Exception as e:
            logging.error(f"Error sending embed image: {e}")

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(TOKEN)
