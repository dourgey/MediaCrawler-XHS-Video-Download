# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：  
# 1. 不得用于任何商业用途。  
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。  
# 3. 不得进行大规模爬取或对平台造成运营干扰。  
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。   
# 5. 不得用于任何非法或不当的用途。
#   
# 详细许可条款请参阅项目根目录下的LICENSE文件。  
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。  
import os
from pathlib import Path
from typing import List
import json

import hashlib
import random
import string
import aiohttp
import aiofiles
import os
from typing import Optional

import asyncio
import sys

import cmd_arg
import config
import db
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.tieba import TieBaCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
from media_platform.zhihu import ZhihuCrawler

#coding=utf-8
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from asyncio import run

from source import XHS


async def download_video(xhs_note_link, download_dir="Download"):
    # 实例对象
    work_path = "./"  # 作品数据/文件保存根路径，默认值：项目根路径
    folder_name = download_dir  # 作品文件储存文件夹名称（自动创建），默认值：Download
    name_format = "作品标题 作品描述"
    user_agent = ""  # User-Agent
    cookie = ""  # 小红书网页版 Cookie，无需登录，可选参数，登录状态对数据采集有影响
    proxy = None  # 网络代理
    timeout = 10  # 请求数据超时限制，单位：秒，默认值：10
    chunk = 1024 * 1024 * 10  # 下载文件时，每次从服务器获取的数据块大小，单位：字节
    max_retry = 5  # 请求数据失败时，重试的最大次数，单位：秒，默认值：5
    record_data = True  # 是否保存作品数据至文件
    image_format = "PNG"  # 图文作品文件下载格式，支持：PNG、WEBP
    folder_mode = False  # 是否将每个作品的文件储存至单独的文件夹
    image_download = False  # 图文作品文件下载开关
    video_download = True  # 视频作品文件下载开关
    live_download = True  # 图文动图文件下载开关
    download_record = True  # 是否记录下载成功的作品 ID
    language = "zh_CN"  # 设置程序提示语言
    read_cookie = None  # 读取浏览器 Cookie，支持设置浏览器名称（字符串）或者浏览器序号（整数），设置为 None 代表不读取
    
    
    async with XHS(
            work_path=work_path,
            folder_name=folder_name,
            name_format=name_format,
            user_agent=user_agent,
            cookie=cookie,
            proxy=proxy,
            timeout=timeout,
            chunk=chunk,
            max_retry=max_retry,
            record_data=record_data,
            image_format=image_format,
            folder_mode=folder_mode,
            image_download=image_download,
            video_download=video_download,
            live_download=live_download,
            download_record=download_record,
            language=language,
            read_cookie=read_cookie,
    ) as xhs:
        return await xhs.extract(xhs_note_link, download=True)


def get_latest_modified_files(directory_path: str, limit: int = 3) -> List[str]:
    """
    获取指定目录下最新修改的文件
    
    Args:
        directory_path (str): 目标目录的路径
        limit (int): 需要获取的文件数量，默认为3
        
    Returns:
        List[str]: 包含最新修改文件绝对路径的列表
    """
    try:
        # 获取目录下所有文件
        files = []
        for file_path in Path(directory_path).rglob('*'):
            if file_path.is_file():
                files.append({
                    'path': str(file_path.absolute()),
                    'mtime': os.path.getmtime(file_path)
                })
        
        # 按修改时间排序并获取前N个
        sorted_files = sorted(files, key=lambda x: x['mtime'], reverse=True)
        return [file['path'] for file in sorted_files[:limit]]
    
    except Exception as e:
        print(f"获取文件列表时出错: {str(e)}")
        return []


async def download_image(url: str, save_dir: str) -> Optional[str]:
    """
    下载图片并使用基于URL的确定性文件名保存，如果文件已存在则跳过下载
    
    Args:
        url (str): 图片的URL
        save_dir (str): 保存图片的目录路径
        
    Returns:
        Optional[str]: 成功则返回生成的文件名，失败则返回None
    """
    try:
        # 使用URL生成确定性的文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        random.seed(url_hash)
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        
        file_extension = '.jpg'
        if '.' in url.split('/')[-1]:
            file_extension = os.path.splitext(url.split('/')[-1])[1]
        
        full_filename = random_name + file_extension
        full_path = os.path.join(save_dir, full_filename)
        
        # 检查文件是否已存在
        if os.path.exists(full_path):
            print(f"文件已存在，跳过下载: {full_filename}")
            return random_name
        
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        # 下载图片
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(full_path, 'wb') as f:
                        await f.write(await response.read())
                    return random_name
                else:
                    print(f"下载图片失败，HTTP状态码: {response.status}")
                    return None
                    
    except Exception as e:
        print(f"下载图片时出错: {str(e)}")
        return None

def download_images_and_videos():
    image_save_dir = "data/xhs/json/images"
    videos_save_dir = "data/xhs/json/videos"

    os.makedirs(image_save_dir, exist_ok=True)
    os.makedirs(videos_save_dir, exist_ok=True)

    async def process_files():
        for file_path in get_latest_modified_files("data/xhs/json"):
            if "creator_comments" in file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for comments in data:
                    # 下载头像
                    avatar_url = comments.get("avatar", "")
                    if avatar_url:
                        avatar_name = await download_image(avatar_url, image_save_dir)
                        if avatar_name:
                            comments["avatar_path"] = os.path.join(image_save_dir, avatar_name)
                    
                    # 下载图片
                    pictures_url = comments.get("pictures", "")
                    if pictures_url:
                        picture_name = await download_image(pictures_url, image_save_dir)
                        if picture_name:
                            comments["pictures_path"] = os.path.join(image_save_dir, picture_name)
                
                # 保存更新后的数据
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

            elif "creator_contents" in file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for content in data:
                    # 下载头像
                    avatar_url = content.get("avatar", "")
                    if avatar_url:
                        avatar_name = await download_image(avatar_url, image_save_dir)
                        if avatar_name:
                            content["avatar_path"] = os.path.join(image_save_dir, avatar_name)
                    
                    # 下载图片列表
                    image_list = content.get("image_list", "")
                    if isinstance(image_list, str) and image_list:
                        image_name = await download_image(image_list, image_save_dir)
                        if image_name:
                            content["image_list_path"] = {image_list: os.path.join(image_save_dir, image_name)}
                    elif isinstance(image_list, list):
                        content["image_list_paths"] = []
                        for img_url in image_list:
                            if img_url:
                                image_name = await download_image(img_url, image_save_dir)
                                if image_name:
                                    content["image_list_paths"].append({img_url: os.path.join(image_save_dir, image_name)})
                    
                    # 下载视频
                    note_url = content.get("note_url", "")
                    if note_url:
                        await download_video(note_url, videos_save_dir)
                        # 获取视频标题
                        title = content.get("title", "")
                        if title:
                            # 遍历视频目录查找匹配的文件
                            for video_file in os.listdir(videos_save_dir):
                                if title in video_file:
                                    # 找到匹配的文件，保存完整路径
                                    content["video_path"] = os.path.join(videos_save_dir, video_file)
                
                # 保存更新后的数据
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

            elif "creator_creator" in file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for creator in data:
                    # 下载头像
                    avatar_url = creator.get("avatar", "")
                    if avatar_url:
                        avatar_name = await download_image(avatar_url, image_save_dir)
                        if avatar_name:
                            creator["avatar_path"] = os.path.join(image_save_dir, avatar_name)
                
                # 保存更新后的数据
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
    
    # 运行异步函数
    asyncio.run(process_files())

class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler,
        "tieba": TieBaCrawler,
        "zhihu": ZhihuCrawler
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported xhs or dy or ks or bili ...")
        return crawler_class()


async def main():
    # parse cmd
    await cmd_arg.parse_cmd()
    print(config)

    # init db
    if config.SAVE_DATA_OPTION == "db":
        await db.init_db()

    crawler = CrawlerFactory.create_crawler(platform=config.PLATFORM)
    await crawler.start()

    if config.SAVE_DATA_OPTION == "db":
        await db.close()

    

if __name__ == '__main__':
    # try:
    #     # asyncio.run(main())
    #     asyncio.get_event_loop().run_until_complete(main())
    # except KeyboardInterrupt:
    #     sys.exit()


    # run(download_video(url))
    download_images_and_videos()