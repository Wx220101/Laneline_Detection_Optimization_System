# 车道线识别精度改进方案

## 1. 当前管线主要误差来源归纳

1. **黑色掩膜单一且受光照干扰**
   - 对应阶段：**预处理（HSV 掩膜）**
   - 当前仅使用黑色 HSV 掩膜（历史曾支持黄/白掩膜但被注释），对路面阴影、逆光、车道线褪色等情况鲁棒性差，容易丢失真实车道线或引入路面沥青等杂散边缘。

2. **直线段碎片化与弯道近似误差**
   - 对应阶段：**几何检测（霍夫变换 + 斜率筛选）**
   - 使用概率霍夫（HoughLinesP）提取直线段，参数 `threshold=50, minLineLength=50, maxLineGap=50` 在弯道场景只能给出局部直线，导致拟合出的车道线在弯道处抖动、偏差大。同时碎片化线段即使聚类也会产生横向误分类（将邻车道线误归入当前车道）。

3. **单侧补偿的像素启发式不可靠**
   - 对应阶段：**偏移估计（单侧二次补偿）**
   - 当只有一条车道线可见时，使用二次多项式拟合并以启发式像素补偿方式推算另一条线，这种补偿在道路宽度变化或转弯时误差明显，且累积偏移会传递到控制端。

4. 辅助性误差来源：
   - ROI 固定比例，不适应上下坡导致的道路消失点变化。
   - 没有时间滤波（帧间跟踪），检测结果跳变。

## 2. 优先推荐的改进措施清单

| 序号 | 措施 | 预期收益 | 实现代价 | 是否需相机标定/透视变换 |
|------|------|----------|----------|------------------------|
| 1 | **启用并融合黄/白掩膜**：恢复被注释的黄色、白色 HSV 掩膜，与黑色掩膜逻辑或融合，或改为 LAB / 梯度增强的方式提取车道标线 | 在阴影、旧路面场景仍能提取到车道线特征，降低漏检 | 低，仅需改动掩膜生成与合并逻辑 | 否 |
| 2 | **引入透视变换（鸟瞰图）+ 滑动窗口多项式拟合** | 消除近大远小畸变，滑动窗口可沿弯道提取连续特征点，多项式拟合更平滑，克服直线逼近的抖动 | 中，需要标定相机内参（或估算消失点）并计算透视矩阵 | 是（至少需离线估算相机内参） |
| 3 | **动态ROI与参数自适应**：基于消失点位置或车辆俯仰角自适应调整 ROI 高度/宽度比例，Canny 双阈值、霍夫参数根据光照亮度动态调整 | 提升上下坡、强弱光切换时的稳定性 | 低-中，需要增加图像亮度统计模块 | 否（仅用图像坐标） |
| 4 | **时间滤波（跟踪）**：对检测到的车道线参数（斜率、截距、多项式系数）进行卡尔曼或移动平均滤波 | 消除帧间跳变，平滑输出 | 低，新增滤波器类 | 否 |

**推荐实施顺序**：先落实 1 和 4（短周期高收益），再推进 2（核心改进），最后考虑 3（锦上添花）。

## 3. 建议的可调参数表

| 参数名（推测） | 当前语义 | 当前值（来自描述） | 建议搜索方向/范围 |
|---------------|----------|-------------------|-------------------|
| `canny_low` | Canny低阈值 | ~50 | 根据场景对比度自动：30–70；晴天下限可提高到60，阴影时降低到40 |
| `canny_high` | Canny高阈值 | ~150 | 配合低阈值调整，保持比例 2:1 到 3:1，如 (40,120) ~ (70,210) |
| `hough_threshold` | 霍夫投票阈值 | 50 | 30–70，降低可提高线段数量但引入噪声，需配合聚类筛选 |
| `hough_min_line_len` | 最小线段长度 | 50px | 30–60px，弯道处可适当降低以捕获短线段 |
| `hough_max_line_gap` | 最大线段间隙 | 50px | 30–70px，增大有利于连接断线 |
| `slope_min` | 斜率绝对值最小阈值 | 0.5 | 0.3–0.7，坡度较小的横向车道可适当放宽 |
| ROI 高/宽比 | 固定值 | 未知 | 根据消失点动态比例，或上下边界占图像高度的 0.4~0.9 |
| 黑色 HSV 范围 | 用于提取地面黑色 | `(0,0,0)~(180,255,50?)` | 重新标定，建议结合形态学膨胀修复车道线区域 |
| 黄/白 HSV 范围 | 已注释 | 历史值 | 恢复并校准，黄色范围：H(10~30) S(50~255) V(100~255)；白色范围：H(0~180) S(0~30) V(180~255) |

注：所有数值应在实际场景录制的 bag 上离线扫描验证。

## 4. 离线/仿真验证建议

1. **录制典型 bag/视频**：在测试沙盘或实际道路录制 rosbag（包含话题 `/camera/image_raw`），覆盖场景：直道、弯道、阴影、强逆光、断续标线。
2. **构建回放测试脚本**：编写 `replay_lane_detector.py`，读取 bag 或视频文件，逐帧调用 `lane_detector`，并保存检测图像或输出左右线参数到 CSV。
3. **量化指标定义**：
   - 车道线存在性检出率（左/右分别统计）
   - 中心偏移误差：与手动标注真值对比
   - 检测稳定性：相邻帧斜率/截距的方差
4. **自动评价**：通过半自动标注工具（如 LabelMe）生成车道线掩膜/边界点，然后计算检测出的曲线与真值的平均欧式距离或 IoU。
5. **参数扫描**：编写脚本自动遍历 Canny 阈值、霍夫参数等组合，在 bag 上运行并输出上述指标，选取 Pareto 前沿。

## 5. 分步实施手册（阶段A可完成）

---

### 步骤 1 — 恢复并融合黄/白车道线掩膜

- **修改文件**：`knowledge/智能车道线检测与保持_彭之芯_吴泓霖_柳阳_42035803/src/catkin_ws/src/lane_follower/scripts/lane_detector.py`
- **定位**：函数 `mask_lane()` 或 `detect_lane()`，搜索关键字 `# yellow`、`# white` 或 `cv2.inRange` 附近。若历史代码被注释，则找到当前黑色掩膜的区域。
- **改什么**：重新激活黄色和白色 HSV 掩膜，并与黑色掩膜通过逻辑或（`cv2.bitwise_or`）合并，以增强对车道标线的提取能力。
- **参考代码**：

  ```python
  # 原有黑色掩膜（假设）
  lower_black = np.array([0, 0, 0])
  upper_black = np.array([180, 255, 50])
  mask_black = cv2.inRange(hsv, lower_black, upper_black)

  # 新增黄色掩膜
  lower_yellow = np.array([10, 50, 100])   # 可根据实际标线微调
  upper_yellow = np.array([40, 255, 255])
  mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

  # 新增白色掩膜
  lower_white = np.array([0, 0, 180])
  upper_white = np.array([180, 30, 255])
  mask_white = cv2.inRange(hsv, lower_white, upper_white)

  # 合并掩膜
  mask_combined = cv2.bitwise_or(mask_black, mask_yellow)
  mask_combined = cv2.bitwise_or(mask_combined, mask_white)

  # 可选：形态学闭运算连接车道线断裂处
  kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
  mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)
  ```

  修改前：
  ```python
  mask = cv2.inRange(hsv, (0,0,0), (180,255,50))  # 仅黑色
  ```
  修改后：
  ```python
  mask = mask_combined   # 使用合并后的掩膜
  ```

- **如何验证**：运行节点并订阅 `lane_detector/debug_mask` 图像（若无可添加发布），观察阴影区域下车道线是否被清晰提取，不再仅依赖黑色路面。

---

### 步骤 2 — 添加帧间卡尔曼滤波器平滑输出

- **修改文件**：同上 `lane_detector.py`
- **定位**：类 `LaneDetector` 的 `__init__` 方法，以及负责计算最终车道线参数的函数（例如 `get_lane_curves()` 或 `process()` 末尾）。
- **改什么**：为左右车道线多项式的系数分别建立一维卡尔曼滤波器，在每帧得到测量值后进行滤波，平滑输出，减少抖动。
- **参考代码**：

  ```python
  import cv2
  import numpy as np

  class LaneDetector:
      def __init__(self):
          # ... 原有初始化
          # 初始化卡尔曼滤波器，以2阶多项式为例 (a_x^2 + b_x + c)
          self.kf_left = cv2.KalmanFilter(3, 3)   # 状态维度3，测量维度3
          self.kf_left.measurementMatrix = np.eye(3, dtype=np.float32)
          self.kf_left.transitionMatrix = np.eye(3, dtype=np.float32)
          self.kf_left.processNoiseCov = np.eye(3, dtype=np.float32) * 1e-4
          self.kf_left.measurementNoiseCov = np.eye(3, dtype=np.float32) * 1e-2
          self.kf_left.errorCovPost = np.eye(3, dtype=np.float32)
          self.left_coeff = None

          # 同理初始化 kf_right
          self.kf_right = cv2.KalmanFilter(3, 3)
          self.kf_right.measurementMatrix = np.eye(3, dtype=np.float32)
          self.kf_right.transitionMatrix = np.eye(3, dtype=np.float32)
          self.kf_right.processNoiseCov = np.eye(3, dtype=np.float32) * 1e-4
          self.kf_right.measurementNoiseCov = np.eye(3, dtype=np.float32) * 1e-2
          self.kf_right.errorCovPost = np.eye(3, dtype=np.float32)
          self.right_coeff = None

      def filter_coefficients(self, measured_coeff, is_left=True):
          kf = self.kf_left if is_left else self.kf_right
          measured = np.array(measured_coeff, dtype=np.float32).reshape(-1,1)
          kf.correct(measured)
          predicted = kf.predict()
          return predicted.flatten()
  ```

  在使用多项式拟合得到系数后调用：
  ```python
  # 原有：left_fit = np.polyfit(lefty, leftx, 2)
  # 修改为：
  if self.left_coeff is None:
      self.left_coeff = left_fit
  else:
      filtered = self.filter_coefficients(left_fit, is_left=True)
      self.left_coeff = filtered
  left_fit = self.left_coeff
  # 同理处理右线
  ```

- **如何验证**：回放录制的视频或 bag，观察检测曲线是否不再高频抖动，尤其在弯道输出更平滑。可在 RVIZ 中对比滤波前后曲线。

---

### 步骤 3 — 引入鸟瞰透视与滑动窗口多项式拟合

鉴于此改进依赖相机标定，分两阶段：先利用离线标定获得透视矩阵，再修改检测流水线。

#### 3.1 离线标定并获得透视矩阵

- **修改文件**：新建脚本 `calibrate_bev.py`（存放在相同目录）
- **定位**：独立脚本，不修改现有节点。
- **改什么**：使用棋盘格标定相机的内参和畸变系数，然后手动选取图像中五个梯形的源点（图像坐标）和对应的鸟瞰图目标点，计算透视变换矩阵 `M`，保存为 `bev_matrix.npy`。
- **参考代码**（关键部分）：
  ```python
  import numpy as np
  import cv2

  # 畸变校正计算（棋盘格拍摄）
  # ... 使用 cv2.calibrateCamera 获取 mtx, dist ...

  # 手动选点获取透视矩阵
  src_pts = np.float32([[...], [...], [...], [...]])  # 图像中梯形四角
  dst_pts = np.float32([[...], [...], [...], [...]])  # 对应鸟瞰矩形
  M = cv2.getPerspectiveTransform(src_pts, dst_pts)
  Minv = cv2.getPerspectiveTransform(dst_pts, src_pts)
  np.save('bev_matrix.npy', {'M': M, 'Minv': Minv, 'mtx': mtx, 'dist': dist})
  ```
  注：梯形选取方法可参照车道线在鸟瞰图中应平行的原则。

#### 3.2 修改 `lane_detector.py` 使用鸟瞰图进行多项式拟合

- **修改文件**：`lane_detector.py`
- **定位**：预处理结束后、Canny/霍夫阶段之前，或者在得到掩膜后直接进行透视变换。搜索 `cv2.Canny` 或 `cv2.HoughLinesP`。
- **改什么**：加载透视矩阵，将掩膜图像变换到鸟瞰视角，然后使用滑动窗口搜索车道线像素并拟合多项式，取代原有的霍夫直线+筛选+二次拟合流程。
- **参考代码**：

  ```python
  class LaneDetector:
      def __init__(self):
          # 加载标定数据
          bev = np.load('bev_matrix.npy', allow_pickle=True).item()
          self.M = bev['M']
          self.Minv = bev['Minv']
          self.mtx = bev.get('mtx', None)
          self.dist = bev.get('dist', None)
          # ... 其余初始化

      def bird_eye_view(self, img):
          return cv2.warpPerspective(img, self.M, (img.shape[1], img.shape[0]))

      def sliding_window_polyfit(self, binary_warped):
          # 取图像下半部分直方图寻找左右车道线起始点
          histogram = np.sum(binary_warped[binary_warped.shape[0]//2:,:], axis=0)
          midpoint = int(histogram.shape[0]/2)
          leftx_base = np.argmax(histogram[:midpoint])
          rightx_base = np.argmax(histogram[midpoint:]) + midpoint

          # 滑动窗口参数
          nwindows = 9
          window_height = np.int(binary_warped.shape[0]/nwindows)
          margin = 100
          minpix = 50

          # 寻找车道线像素
          nonzero = binary_warped.nonzero()
          nonzeroy = np.array(nonzero[0])
          nonzerox = np.array(nonzero[1])
          leftx_current = leftx_base
          rightx_current = rightx_base

          left_lane_inds = []
          right_lane_inds = []

          for window in range(nwindows):
              win_y_low = binary_warped.shape[0] - (window+1)*window_height
              win_y_high = binary_warped.shape[0] - window*window_height
              # 左窗口范围
              win_xleft_low = leftx_current - margin
              win_xleft_high = leftx_current + margin
              # 右窗口范围
              win_xright_low = rightx_current - margin
              win_xright_high = rightx_current + margin

              good_left = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                           (nonzerox >= win_xleft_low) & (nonzerox < win_xleft_high)).nonzero()[0]
              good_right = ((nonzeroy >= win_y_low) & (nonzeroy < win_y_high) &
                            (nonzerox >= win_xright_low) & (nonzerox < win_xright_high)).nonzero()[0]

              left_lane_inds.append(good_left)
              right_lane_inds.append(good_right)

              if len(good_left) > minpix:
                  leftx_current = np.int(np.mean(nonzerox[good_left]))
              if len(good_right) > minpix:
                  rightx_current = np.int(np.mean(nonzerox[good_right]))

          left_lane_inds = np.concatenate(left_lane_inds)
          right_lane_inds = np.concatenate(right_lane_inds)

          leftx = nonzerox[left_lane_inds]
          lefty = nonzeroy[left_lane_inds]
          rightx = nonzerox[right_lane_inds]
          righty = nonzeroy[right_lane_inds]

          # 二次多项式拟合
          left_fit = np.polyfit(lefty, leftx, 2) if len(lefty) > 0 else None
          right_fit = np.polyfit(righty, rightx, 2) if len(righty) > 0 else None
          return left_fit, right_fit

      # 在 process 中调用：
      # binary = mask_combined  # 步骤1后的掩膜
      # warped = self.bird_eye_view(binary)
      # left_fit, right_fit = self.sliding_window_polyfit(warped)
  ```

  注：需移除原有的 `HoughLinesP` 调用及斜率筛选等，可保留作为退化方案。

- **如何验证**：使用标定后的图像和 `bev_matrix.npy`，在节点中画出鸟瞰图上的滑动窗口和拟合曲线，观察是否贴合弯道处车道线；然后在原图上绘制通过 `Minv` 反投影的曲线，与真实车道线对比。

---

以上三步可在预计 1-2 个迭代内完成代码修改与离线调优，结合 bag 回放量化评估，实现显著精度提升。

（全文结束）