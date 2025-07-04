import os
from os.path import getsize
import hashlib
import requests
from bs4 import BeautifulSoup
from Module.config import HEADERS

class ImageHandler:
    def __init__(self):
        if not os.path.exists("Image"):
            os.makedirs("Image")

    def download_image(self, url):
        """이미지 다운로드"""
        try:
            headers = HEADERS.copy()
            headers['Referer'] = url
            
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # 이미지 링크 찾기 (수정된 선택자)          
            image_download_contents = soup.select("div.appending_file_box ul li")
            for li in image_download_contents:
                img_tag = li.find('a', href=True)
                img_url = img_tag['href']

                file_ext = img_url.split('.')[-1]
                # 저장될 파일명
                savename = img_url.split("no=")[2]
                headers['Referer'] = url
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
                
            return None
            
        except Exception as e:
            return None
"""
    def calculate_hash(self, file_path):
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            return None
"""