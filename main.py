import sensor
import time
import image

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QVGA)
sensor.set_vflip(True)
sensor.set_hmirror(True)
sensor.skip_frames(time=2000)

# 加载人脸检测模型
face_cascade = image.HaarCascade("frontalface", stages=25)
print("Loaded Face Cascade Model")

clock = time.clock()


# 优化的表情识别函数 - 减少fear误判
def detect_emotion(face_roi):
    # 图像预处理
    face_roi = face_roi.histeq()  # 增强对比度
    face_roi = face_roi.gaussian(1)  # 降噪

    # 调整区域划分比例，更准确提取五官
    # 眼睛区域（更精确的比例）
    eye_y = int(face_roi.height() * 0.22)
    eye_height = int(face_roi.height() * 0.22)
    left_eye_roi = (int(face_roi.width() * 0.12), eye_y,
                    int(face_roi.width() * 0.38), eye_height)
    right_eye_roi = (int(face_roi.width() * 0.5), eye_y,
                     int(face_roi.width() * 0.38), eye_height)

    # 嘴巴区域（调整位置和大小）
    mouth_y = int(face_roi.height() * 0.62)
    mouth_height = int(face_roi.height() * 0.32)
    mouth_roi = (int(face_roi.width() * 0.18), mouth_y,
                 int(face_roi.width() * 0.64), mouth_height)

    # 提取区域并计算特征
    left_eye = face_roi.copy(roi=left_eye_roi)
    right_eye = face_roi.copy(roi=right_eye_roi)
    mouth = face_roi.copy(roi=mouth_roi)

    # 计算统计特征
    left_stats = left_eye.get_histogram().get_statistics()
    right_stats = right_eye.get_histogram().get_statistics()
    mouth_stats = mouth.get_histogram().get_statistics()

    # 提取关键特征（扩大有效范围）
    left_eye_brightness = left_stats[0]
    right_eye_brightness = right_stats[0]
    mouth_brightness = mouth_stats[0]

    left_eye_contrast = left_stats[6]
    right_eye_contrast = right_stats[6]
    mouth_contrast = mouth_stats[6]

    # 双眼对称性（扩大可接受范围）
    symmetry = abs(left_eye_brightness - right_eye_brightness)

    # 重新排序判断条件，优先识别常见表情
    # 1. 中性表情（最常见，优先判断）
    if (90 < mouth_brightness < 140 and
            30 < mouth_contrast < 70 and
            80 < left_eye_brightness < 150 and
            80 < right_eye_brightness < 150 and
            symmetry < 35):
        return "neutral"

    # 2. 开心（笑脸特征明显，次优先）
    elif (110 < mouth_brightness < 180 and
          50 < mouth_contrast < 90 and
          symmetry < 30):
        return "happy"

    # 3. 惊讶（眼睛特征明显）
    elif (130 < left_eye_brightness < 200 and
          130 < right_eye_brightness < 200 and
          symmetry < 25 and
          40 < mouth_contrast < 80):
        return "surprised"

    # 4. 悲伤（调整阈值范围）
    elif (60 < mouth_brightness < 110 and
          20 < mouth_contrast < 50 and
          symmetry < 35):
        return "sad"

    # 5. 愤怒（调整判断条件）
    elif (mouth_contrast > 60 and
          symmetry > 25 and
          70 < left_eye_brightness < 150 and
          70 < right_eye_brightness < 150):
        return "angry"

    # 6. 恐惧（最后判断，减少误判）
    elif (mouth_brightness < 80 and
          mouth_contrast > 70 and
          symmetry > 30):
        return "fear"

    # 无法明确分类的情况归为中性而非恐惧
    else:
        return "neutral"


# 平滑表情结果
class EmotionSmoother:
    def __init__(self, buffer_size=5):
        self.buffer_size = buffer_size
        self.buffer = []
        self.emotion_map = {
            "happy": 0, "sad": 1, "surprised": 2,
            "angry": 3, "neutral": 4, "fear": 5
        }
        self.reverse_emotion_map = {v: k for k, v in self.emotion_map.items()}

    def update(self, emotion):
        self.buffer.append(self.emotion_map[emotion])
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

        # 计算最频繁出现的表情
        counts = {}
        for e in self.buffer:
            counts[e] = counts.get(e, 0) + 1
        most_common = max(counts, key=counts.get)
        return self.reverse_emotion_map[most_common]


# 创建平滑器实例
emotion_smoother = EmotionSmoother(buffer_size=4)  # 减小缓冲大小，提高响应速度

while True:
    clock.tick()
    img = sensor.snapshot()

    # 执行人脸检测
    faces = img.find_features(face_cascade,
                              threshold=0.68,  # 适度降低阈值，提高检测率
                              scale_factor=1.2,
                              min_neighbors=2,
                              roi=(40, 30, 240, 180))

    if faces:
        for face in faces:
            x, y, w, h = face
            img.draw_rectangle(face, color=(255), thickness=2)
            center_x = x + w // 2
            center_y = y + h // 2
            img.draw_cross(center_x, center_y, color=(255), size=5)

            # 提取人脸区域
            face_roi = img.copy(roi=face)
            emotion = detect_emotion(face_roi)
            smoothed_emotion = emotion_smoother.update(emotion)

            # 显示结果
            img.draw_string(x, y - 15, smoothed_emotion, color=(255), scale=2)
            print("[DETECTED] Face: %dx%d | Emotion: %s | FPS: %.1f" %
                  (w, h, smoothed_emotion, clock.fps()))
    else:
        print("[SCANNING] FPS: %.1f" % clock.fps())

    # 显示帧率
    fps_text = "FPS: {:.1f}".format(clock.fps())
    img.draw_string(10, 10, fps_text, color=(255), scale=2)
