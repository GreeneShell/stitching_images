import os

from loguru import logger


def get_images(folder_path):
    image_count = 0
    png_files = []
    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(".png") or file.lower().endswith(".jpg"):
                    png_files.append(os.path.join(root, file))
                    image_count += 1
                    logger.info(f"已找到 {image_count} 张图片")
    except FileNotFoundError:
        print(f"错误：未找到文件夹 {folder_path}。")
    except Exception as e:
        print(f"发生未知错误：{e}")
    return png_files
