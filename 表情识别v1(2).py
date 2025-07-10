import pyautogui
import time
import os
import glob
from fer import FER
import cv2
import pygame
import random
from pygame import mixer

# 配置参数（可根据需要修改）
REGION = (2000, 160, 550, 300)  # 截图区域 (x, y, 宽度, 高度)
CYCLE_INTERVAL = 20  # 循环周期（秒）
SCREENSHOT_COUNT = 3  # 固定为3，对应x、y、z三个变量
SHOT_INTERVAL = 2  # 截图间隔（秒）
FILE_PREFIX = "pyautogui_screenshot_"  # 截图文件前缀
FADE_OUT_DURATION = 2  # 音乐淡出时间（秒）
FADE_IN_DURATION = 2  # 音乐淡入时间（秒）
VOLUME_CHANGE_STEP = 0.05  # 音量调整步长
VOLUME_CHANGE_INTERVAL = 0.1  # 音量调整间隔（秒）

# 音乐文件路径（请根据你的实际路径修改）
music_files = {
    "happy": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/高兴/《The Promise》快乐.mp3"
    ],
    "sad": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/伤心/《A Time For Us》悲伤.mp3"
    ],
    "angry": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/愤怒/《月光边境》愤怒.mp3"
    ],
    "surprise": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/惊喜/《月光奏鸣曲 》惊讶.mp3"
    ],
    "fear": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/恐惧/《夏·烟火》恐惧.mp3"
    ],
    "disgust": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/厌烦/《森林狂想曲》厌恶.mp3"
    ],
    "neutral": [
        "C:/Users/ASUS/Desktop/AI导论实验/大作业/音乐集/寻常/《阿尔法波》中性.mp3"
    ],
}

# 初始化pygame混音器
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
current_emotion = None
current_volume = 1.0  # 初始音量为最大


def delete_previous_screenshots():
    """删除上一次循环产生的所有截图"""
    screenshot_files = glob.glob(f"{FILE_PREFIX}*.png")
    for file in screenshot_files:
        try:
            os.remove(file)
            print(f"已删除旧截图：{os.path.basename(file)}")
        except OSError as e:
            print(f"删除文件失败 {file}：{e}")


def capture_screenshots():
    """捕获3张截图，返回包含完整路径的列表（长度固定为3）"""
    screenshot_paths = []
    for i in range(SCREENSHOT_COUNT):
        timestamp = time.strftime("%Y%m%d_%H%M%S") + f"_{int(time.time() * 1000) % 1000}"
        filename = f"{FILE_PREFIX}{timestamp}.png"
        full_path = os.path.abspath(filename)  # 获取完整路径
        # 截取并保存截图
        screenshot = pyautogui.screenshot(region=REGION)
        screenshot.save(full_path)
        screenshot_paths.append(full_path)
        print(f"已保存截图 {i + 1}/{SCREENSHOT_COUNT}：{os.path.basename(full_path)}")
        # 非最后一张截图等待间隔
        if i != SCREENSHOT_COUNT - 1:
            time.sleep(SHOT_INTERVAL)
    return screenshot_paths


def analyze_emotions(image_path):
    """使用FER分析图片中的面部情绪"""
    try:
        # 初始化FER检测器
        detector = FER(mtcnn=False)

        # 读取图像
        image = cv2.imread(image_path)

        # 检测情绪
        results = detector.detect_emotions(image)

        if not results:
            return None

        # 返回第一个检测到的人脸情绪（可根据需要修改为处理多张人脸）
        return results[0]["emotions"]
    except Exception as e:
        print(f"情绪分析出错 ({image_path}): {str(e)}")
        return None


def fade_out_music():
    """淡出当前播放的音乐"""
    global current_volume
    if pygame.mixer.music.get_busy():
        steps = int(FADE_OUT_DURATION / VOLUME_CHANGE_INTERVAL)
        step_size = current_volume / steps

        for _ in range(steps):
            current_volume = max(0, current_volume - step_size)
            pygame.mixer.music.set_volume(current_volume)
            time.sleep(VOLUME_CHANGE_INTERVAL)

        pygame.mixer.music.stop()
        current_volume = 0.0


def fade_in_music():
    """淡入当前播放的音乐"""
    global current_volume
    target_volume = 1.0
    steps = int(FADE_IN_DURATION / VOLUME_CHANGE_INTERVAL)
    step_size = target_volume / steps

    for _ in range(steps):
        current_volume = min(target_volume, current_volume + step_size)
        pygame.mixer.music.set_volume(current_volume)
        time.sleep(VOLUME_CHANGE_INTERVAL)


def play_emotion_music(emotion):
    """根据情绪播放对应的音乐，带平滑过渡效果"""
    global current_emotion, current_volume

    # 如果情绪没有变化，不做任何操作
    if emotion == current_emotion:
        return

    # 检查是否有对应情绪的音乐文件
    if emotion not in music_files or not music_files[emotion]:
        print(f"没有为情绪 '{emotion}' 配置的音乐文件")
        return

    # 随机选择一首音乐
    path = random.choice(music_files[emotion])
    if not os.path.exists(path):
        print(f"音乐文件不存在: {path}")
        return

    try:
        print(f"准备播放 {emotion} 音乐... ({path})")

        # 淡出当前音乐
        if pygame.mixer.music.get_busy():
            fade_out_music()

        # 加载并播放新音乐（初始音量为0）
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.play(-1)  # -1表示循环播放

        # 淡入新音乐
        fade_in_music()

        # 更新当前情绪状态
        current_emotion = emotion
        print(f"正在播放 {emotion} 音乐")

    except pygame.error as e:
        print(f"播放音乐时出错(Pygame错误): {e}")
    except Exception as e:
        print(f"播放音乐时出错: {e}")


def determine_dominant_emotion(emotions_list):
    """根据三张图片的情绪分析结果确定主导情绪"""
    if not emotions_list or len(emotions_list) != 3:
        return "neutral"

    # 合并三张图片的情绪数据
    combined_emotions = {
        "angry": 0,
        "disgust": 0,
        "fear": 0,
        "happy": 0,
        "sad": 0,
        "surprise": 0,
        "neutral": 0
    }

    for emotions in emotions_list:
        if emotions:
            for emotion, score in emotions.items():
                combined_emotions[emotion] += score

    # 找出主导情绪
    dominant_emotion = max(combined_emotions.items(), key=lambda item: item[1])[0]
    return dominant_emotion


def main():
    print("程序启动，按 Ctrl+C 停止...")
    try:
        while True:
            print("\n===== 开始新的循环 =====")

            # 1. 删除上一次循环的截图
            delete_previous_screenshots()

            # 2. 捕获3张截图，获取路径列表并赋值给x、y、z
            screenshot_paths = capture_screenshots()
            x, y, z = screenshot_paths  # 解包：x=第1张，y=第2张，z=第3张

            # 3. 打印3张截图的地址（方便确认变量对应关系）
            print("\n本轮截图地址变量：")
            print(f"x（第1张截图地址）：{x}")
            print(f"y（第2张截图地址）：{y}")
            print(f"z（第3张截图地址）：{z}")

            # 4. 对每张图片进行情绪分析
            print("\n开始情绪分析...")
            emotions_list = []

            for i, path in enumerate([x, y, z]):
                emotions = analyze_emotions(path)
                emotions_list.append(emotions)
                if emotions:
                    print(f"\n图片 {['x', 'y', 'z'][i]} 检测到情绪:")
                    for emotion, score in emotions.items():
                        print(f"{emotion}: {score:.2f}")

                    # 找出最可能的情绪
                    dominant_emotion = max(emotions.items(), key=lambda item: item[1])
                    print(f"主要情绪: {dominant_emotion[0]} (置信度: {dominant_emotion[1]:.2f})")
                else:
                    print(f"\n图片 {['x', 'y', 'z'][i]} 未检测到人脸或分析失败")

            # 5. 根据三张图片的情绪分析结果确定主导情绪并播放音乐
            dominant_emotion = determine_dominant_emotion(emotions_list)
            print(f"\n主导情绪确定为: {dominant_emotion}")
            play_emotion_music(dominant_emotion)

            # 6. 计算等待时间，确保总周期为20秒
            wait_time = CYCLE_INTERVAL - (SHOT_INTERVAL * (SCREENSHOT_COUNT - 1))
            print(f"\n等待 {wait_time} 秒进入下一轮...")
            time.sleep(wait_time)

    except KeyboardInterrupt:
        print("\n程序已手动停止")
    finally:
        delete_previous_screenshots()
        # 停止音乐播放
        pygame.mixer.music.stop()
        print("所有临时截图已清理，音乐已停止")


if __name__ == "__main__":
    main()