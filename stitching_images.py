import os
import time
from loguru import logger
from PIL import Image


def is_image_exists(image_list: list) -> bool:
    """
    判断图片是否存在
    Args:
        image_list(list): 图片路径列表
    Returns:
        bool, 是否存在
    """
    for image in image_list:
        if not os.path.exists(image):
            return False
    return True


def preprocess(
    image_list: list, header_height: int, footer_height: int, output_path: str, ext: str
) -> tuple:
    """
    图片预处理
    Args:
        image_list(list): 图片路径列表
        header_height(int): 头部高度
        footer_height(int): 尾部高度
        output_path(str): 处理后图片的输出目录
        ext(str): 图片格式
    Returns:
        tuple: 原始图片列表和处理后的图片列表
    """
    origin_image_list = []
    processed_image_list = []
    i = 0
    for image in image_list:
        i += 1
        # 打开图片
        img = Image.open(image)
        origin_image_list.append(img)
        # 转换为灰度图
        img = img.convert("L")
        # 剪裁头尾, header_height & footer_height
        img = img.crop((0, header_height, img.width, img.height - footer_height))
        # 保存图片到临时文件夹
        img.save(os.path.join(output_path, f"1-{i}.{ext}"))
        processed_image_list.append(img)
    return origin_image_list, processed_image_list


def get_columns_color(img: Image, columns: list) -> list:
    """
    获取指定列的颜色
    Args:
        img(Image): 图片
        columns(list): 指定的图片列
    Returns:
        list(list): 图片每列的颜色列表
    """
    columns_colors = []
    for column in columns:
        column_colors = []
        for row in range(img.height):
            color = img.getpixel((column, row))
            column_colors.append(color)
        columns_colors.append(column_colors)
    return columns_colors


def calc_average_absolute_deviation(list1: list, list2: list, shift: int) -> tuple:
    """
    计算平均绝对偏差
    Args:
        list1(list): 列表1
        list2(list): 列表2
        shift(int): 偏移量
    Returns:
        tuple: 偏移量和平均绝对偏差
    """
    total_diff = 0
    count_pixels = 0

    for column in range(len(list1)):
        column1 = list1[column]
        column2 = list2[column]
        sum_column_diff = 0
        count_pixel = 0
        for y_pixel in range(shift, len(column1)):
            sum_column_diff += abs(column1[y_pixel] - column2[y_pixel - shift])
            count_pixel += 1
        total_diff += sum_column_diff
        count_pixels += count_pixel

    return shift, (total_diff // count_pixels)


def find_coincidence(list1: list, list2: list) -> int:
    """
    寻找重合列
    Args:
        list1(list): 颜色灰度值列表1
        list2(list): 颜色灰度值列表2
    Returns:
        int: 偏移量
    """
    sum_diff_list = []
    for i in range(0, len(list1[0])):
        diff = calc_average_absolute_deviation(list1, list2, i)
        sum_diff_list.append(diff)

    # 查找"平均绝对差"最小的值， min_diff = （<偏移值>，<平均绝对差>）
    min_diff = sum_diff_list[0]
    for diff in sum_diff_list:
        if diff[1] < min_diff[1]:
            min_diff = diff

    logger.info(min_diff)
    return min_diff[0]


def remove_black_bottom(image_path: str, output_path: str):
    """
    去除图片底部黑色部分
    Args:
        image_path(str): 图片路径
        output_path(str): 输出路径
    """
    # 打开图片
    img = Image.open(image_path)
    # 转换为灰度图
    gray_img = img.convert("L")
    width, height = img.size
    # 从下往上扫描，找到第一个非黑色像素的位置
    for y in range(height - 1, -1, -1):
        row_is_black = True
        for x in range(width):
            if gray_img.getpixel((x, y)) > 5:  # 如果像素值大于5，则认为不是黑色
                row_is_black = False
                break
        if not row_is_black:
            break
    # 裁剪图片
    cropped_img = img.crop((0, 0, width, y + 1))
    # 保存裁剪后的图片
    cropped_img.save(output_path)


def stitching_images(
    image_list: list,
    output_path: str = None,
    header_height: int = 255,
    footer_height: int = 300,
    x_columns=None,
    ext: str = "png",
):
    """
    图片拼接
    Args:
        image_list(list): 图片路径列表
        output_path(str): 拼接后图片的输出路径
        header_height(int): 头部高度
        footer_height(int): 尾部高度
        x_columns(list): 指定对比的列的x坐标
        ext(str): 图片格式
    """
    # 判断图片是否存在
    if x_columns is None:
        x_columns = [240, 540, 960]
    if not is_image_exists(image_list):
        return "图片不存在！！！"
    # 设置临时目录
    root_path = os.path.abspath(os.path.join(__file__, "../"))
    tmp_dir = os.path.join(root_path, "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    # 设置默认输出路径
    if output_path is None:
        output_path = os.path.join(root_path, "out.png")
    # 图片预处理
    origin_image_list, processed_image_list = preprocess(
        image_list, header_height, footer_height, tmp_dir, ext
    )
    origin_img1 = origin_image_list[0]
    next_image_top = 0
    last_columns_colors = get_columns_color(processed_image_list[0], x_columns)
    # 创建足够大的画布
    long_img = Image.new(
        "RGB", (origin_img1.width, origin_img1.height * len(origin_image_list) * 2)
    )

    # 添加第一张图片
    header = origin_img1.crop(
        (0, 0, origin_img1.width, origin_img1.height - footer_height)
    )
    long_img.paste(header, (0, 0, header.width, header.height))
    long_img.save(os.path.join(tmp_dir, f"2-0.{ext}"))
    next_image_top += header.height
    # 处理剩余的图片
    for i in range(1, len(processed_image_list)):
        logger.info(f"处理第 {i + 1} 张图片")
        t1 = time.time()

        # 获取当前图片的颜色列表
        current_columns_colors = get_columns_color(processed_image_list[i], x_columns)
        # 查找最佳重合位置
        shift = find_coincidence(last_columns_colors, current_columns_colors)
        # 更新用于对比的颜色列表
        last_columns_colors = current_columns_colors
        # 更新顶部位置
        next_image_top += shift
        # 获取原始图片
        origin_img = origin_image_list[i]
        # 裁剪并粘贴内容
        img_content = origin_img.crop(
            (0, header_height, origin_img.width, origin_img.height - footer_height)
        )
        long_img.paste(
            img_content,
            (0, next_image_top - img_content.height, img_content.width, next_image_top),
        )

        # 保存中间结果
        long_img.save(os.path.join(tmp_dir, f"2-{i + 1}.{ext}"))

        t2 = time.time()
        logger.info(f"处理耗时: {t2 - t1:.2f} 秒")
    footer_img = origin_image_list[-1]
    footer = footer_img.crop(
        (0, footer_img.height - footer_height, footer_img.width, footer_img.height)
    )
    long_img.paste(
        footer, (0, next_image_top, footer.width, next_image_top + footer.height)
    )
    next_image_top += footer.height
    final_image_path = os.path.join(tmp_dir, f"2-end.{ext}")
    long_img.save(final_image_path)
    remove_black_bottom(final_image_path, output_path)
    logger.info(f"拼接完成，保存路径为：{output_path}")


if __name__ == "__main__":
    import get_images

    images = get_images.get_images("./images")
    stitching_images(images, header_height=390, footer_height=200)
