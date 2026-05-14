# 车道线识别精度改进方案

## 1 当前管线的主要误差来源归纳

基于现有 `lane_detector` 节点的实现分析，识别出以下三大误差来源，按处理阶段对应：

### 1.1 颜色掩膜失效导致的错误检测或漏检
- **阶段**：预处理（BGR→HSV，掩膜）
- **现象**：当前仅使用黑色 HSV 掩膜（黄/白掩膜被注释），对车道线颜色变化的适应性极差。路面阴影、沥青新旧、雨天反光等场景下黑色掩膜无法稳定提取车道线区域，造成大量漏检；同时道路上其他黑色物体（如车辆阴影、轮胎印）会被误认为车道线，产生大量噪声线段。
- **后果**：有效边缘信息严重不足，霍夫变换输入质量差，直接导致左右线数量稀少或错误线段混入，进而引起车道中心计算跳动甚至完全丢失。

### 1.2 霍夫直线参数固定导致的线段碎片化与误检
- **阶段**：几何（概率霍夫变换）
- **现象**：`HoughLinesP` 使用全局固定参数 `threshold=50, minLineLength=50, maxLineGap=50`。在弯道处，由于车道线曲率，长线段难以形成，只能检测出一系列短线段（碎片）；在强纹理路面（如沥青颗粒、接缝），低阈值易引入大量干扰直线；在车道线部分被遮挡或磨损时，间隙大于 50 像素会导致线段断裂。
- **后果**：碎片化的线段经斜率筛选后，左右线数量不足或混入错误斜率的线段，后续拟合不稳定，表现为检测框抖动、弯道中车道线丢失。

### 1.3 单帧独立处理与缺乏时序平滑
- **阶段**：后处理（左右线选择与偏移计算）
- **现象**：每一帧单独进行线段筛选、单侧二次拟合或启发式像素补偿，没有利用帧间连续性。当某一帧出现瞬时误检（如相邻车道线干扰、光照突变）时，输出的车道中心会剧烈跳变，即使相邻帧检测正确，系统也无法自我纠正。
- **后果**：控制指令抖动，影响方向盘平稳性，尤其在弯道或光照变化频繁路段体感明显。

## 2 优先推荐的改进措施清单

根据误差来源和工程可实现性，按优先级排序：

| 优先级 | 改进措施 | 预期收益 | 实现代价 | 是否需要额外标定/变换 |
|--------|----------|----------|----------|----------------------|
| 1 | 启用并调优黄/白多通道掩膜（修复注释代码），结合黑色掩膜形成互补掩膜策略 | 大幅提升车道线检出率，减少阴影干扰，是后续一切处理的基础 | 低（约 50 行代码，以现有被注释逻辑为基础调整） | 否，仅颜色阈值调试 |
| 2 | 动态调整霍夫参数（基于 ROI 宽度或车速）并引入线段聚类（空间‑角度亲和性） | 减少碎片化，将属于同一直道线的短线段合并为长线段，拟合更稳定 | 中（约 80 行，需实现简单 DBSCAN 或角度‑距离聚类） | 否 |
| 3 | 在单侧补偿中引入帧间低通滤波（指数移动平均） | 消除瞬时抖动，输出平滑车道中心 | 低（约 10 行） | 否 |
| 4 | 加入局部 ROI 自适应策略（根据上一帧检测结果缩小下一帧 ROI） | 排除干扰，加速检测，减轻弯道丢失 | 中（约 60 行） | 否 |
| 5 | 引入鸟瞰逆透视变换（IPM）与多项式拟合 | 彻底解决弯道近似误差，输出 3 阶多项式车道线 | 高（需标定相机并进行透视变换，改动较大） | 需要相机内参标定、安装高度测量 |

以上措施 1~3 属于**阶段 A** 内可完成的感知侧改动，无需改动标定或引入新变换，立即落地。措施 4 为中期优化，措施 5 为长期重构方案，本报告不展开。

## 3 建议的可调参数表

以下参数基于当前 `lane_detector.py` 中可定位的变量/常量，给出语义与建议搜索方向。

| 参数名（推测或建议添加） | 当前语义 | 建议搜索方向或范围 | 备注 |
|--------------------------|----------|---------------------|------|
| `LOWER_BLACK/ UPPER_BLACK` | 黑色 HSV 掩膜阈值（如 [0,0,0] ~ [180,255,50]） | 实际路面采样后微调 V 通道上限，避免噪声 | 当前值未知，需查看脚本确认并采样优化 |
| `LOWER_YELLOW/ UPPER_YELLOW` | 黄色掩膜（注释状态） | 解开注释，标准范围 H [15,45], S [60,255], V [100,255] 根据相机微调 | 务必与白色掩膜同时使用 |
| `LOWER_WHITE/ UPPER_WHITE` | 白色掩膜（注释状态） | 解开注释，标准范围 H [0,180], S [0,30], V [200,255] 根据光照调整 | – |
| `CANNY_LOW, CANNY_HIGH` | Canny 双阈值 `(50,150)` | 低阈值搜索 [30, 70]，高阈值 [120, 200]，可尝试根据 ROI 亮度直方图自适应 | 自适应可用 `cv2.mean()` 计算 ROI 平均亮度动态计算 |
| `HOUGH_THRESHOLD` | 霍夫投票阈值 `50` | 搜索 [30, 80]，考虑与 ROI 像素总数成比例（如 `int(0.05 * ROI_height)`） | 调整以平衡误检与漏检 |
| `MIN_LINE_LENGTH` | 最小线段长度 `50` | 建议与图像高度比例挂钩，如 `int(0.08 * img_height)`，范围约 40–80 | – |
| `MAX_LINE_GAP` | 线段间最大间隙 `50` | 建议放大至 80–120，以减少碎片，配合聚类使用 | 过大可能连接不同线 |
| `SLOPE_THRESH` | 斜率绝对值下限 `0.5` | 可扩大至 `0.3` 以包含小曲率弯道线（但需位置筛选加强） | 配合 ROIR2 位置判别 |
| `CLUSTER_EPS` (新增) | 线段聚类的距离阈值（像素） | 建议 20–50 像素 | 需权衡 |
| `CLUSTER_ANGLE_EPS` (新增) | 角度差阈值（度） | 建议 5–10 度 | – |
| `EMA_ALPHA` (新增) | 中心偏移的指数平滑系数 | 推荐 0.2–0.4 | 越大越平滑，但响应变慢 |

## 4 离线/仿真验证建议

为客观评价改进效果并避免上车风险，建议采用以下验证流程：

1. **录制真实场景 rosbag 或视频序列**  
   - 录制典型场景：直道、上下坡、弯道（急/缓）、光照变化（进出隧道/树荫）、路面有积水/阴影等。
   - 使用 `rosbag record /image_raw /vehicle_speed` 记录所有需要的 topic。
   - 若无 ROS 环境，使用摄像头直接录制 MP4 视频，并编写一个读取视频帧的 `image_publisher` 或直接修改节点输入源为视频文件。

2. **建立标注真值（可选简易版）**  
   - 抽样关键帧，人工标注左右车道线关键点或车道中心位置（可使用工具如 `labelme` 画线并导出坐标）。
   - 计算误差指标：平均中心偏移误差（像素）、检测成功率（连续 N 帧有合理输出）等。

3. **回放测试与指标自动化**  
   - 修改节点启动文件，将输入改为 bag 回放或视频文件。
   - 在脚本中添加性能记录代码：每帧输出左右线数量、斜率、中心偏移等，保存到 CSV。
   - 使用脚本分析 CSV，统计检测丢失率、中心偏移标准差等。

4. **对比实验**  
   - 分别运行原始参数和优化参数，生成两套 CSV，用 Python 绘图比较（如折线图叠加）。
   - 定义提升目标：中心偏移标准差降低 30% 以上，丢失率降低 50% 以上。

## 5 分步实施手册（阶段 A 内可完成的感知侧改动）

以下步骤均可直接在 `lane_detector.py` 中修改完成，无需改动其他节点或硬件。修改前建议备份原文件。

### 步骤 1 — 启用并调优黄/白掩膜，形成多色融合检测

- **修改文件**：`lane_follower/scripts/lane_detector.py`
- **定位**：搜索“`#lower_yellow`”或“`#mask_yellow`”，通常位于一个名为 `preprocess` 或 `extract_lane` 的函数内，预计在 60–120 行区间。
- **改什么**：将原本注释掉的黄色和白色 HSV 掩膜代码恢复，并与黑色掩膜进行逻辑或 (`cv2.bitwise_or`)，得到更完整的车道区域。
- **参考代码**：

```python
def preprocess_image(img_bgr):
    # 原有代码：转换为 HSV
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # === 黑色掩膜（保留原有逻辑）===
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 50])
    mask_black = cv2.inRange(img_hsv, lower_black, upper_black)

    # === 黄色掩膜（新启用，阈值建议先使用以下值）===
    lower_yellow = np.array([15, 60, 100])
    upper_yellow = np.array([45, 255, 255])
    mask_yellow = cv2.inRange(img_hsv, lower_yellow, upper_yellow)

    # === 白色掩膜（新启用）===
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask_white = cv2.inRange(img_hsv, lower_white, upper_white)

    # 融合掩膜：车道线 = 黄色 | 白色 | 黑色（车道对比度对象，可根据需要调整）
    mask_combined = cv2.bitwise_or(mask_black, mask_yellow)
    mask_combined = cv2.bitwise_or(mask_combined, mask_white)

    # 形态学去噪（可选）
    kernel = np.ones((3,3), np.uint8)
    mask_combined = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)

    # 将掩膜应用到原图或灰度图
    img_masked = cv2.bitwise_and(img_bgr, img_bgr, mask=mask_combined)
    gray = cv2.cvtColor(img_masked, cv2.COLOR_BGR2GRAY)

    # 后续继续执行 Canny 等
    return gray, mask_combined   # 返回灰度图和掩膜以供调试显示
```

- **如何验证**：运行节点，通过 `cv2.imshow("Mask Combined", mask_combined)` 可视化掩膜，观察在不同路面（包括有阴影和标线磨损）下车道线是否被完整提取。确认没有大幅增加无关噪声后，记录一次完整 rosbag 回放，查看车道线检测框数是否明显增加。

### 步骤 2 — 引入线段聚类，将碎片线段合并为长线段

- **修改文件**：`lane_follower/scripts/lane_detector.py`
- **定位**：函数 `detect_lanes` 或 `hough_lines` 附近，通常在概率霍夫变换得到 `lines` 列表后，斜率筛选之前。
- **改什么**：在斜率筛选之前，先将所有线段按端点的角度和空间距离进行聚类，每个类用一个平均线段代替，以减少碎片化，增加后续拟合的稳定性。
- **参考代码**：

在脚本顶部增加辅助函数：

```python
def cluster_lines(lines, angle_thresh=10.0, dist_thresh=50.0):
    """
    将线段按角度相似性和端点空间距离聚类，返回代表性线段列表。
    lines: (N,1,4) 霍夫输出
    """
    if lines is None:
        return []
    lines = lines.reshape(-1, 4)  # (N,4)
    # 计算每条线的角度（度）和中点
    angles = []
    midpoints = []
    for x1,y1,x2,y2 in lines:
        angle = np.arctan2(y2-y1, x2-x1) * 180.0 / np.pi
        angles.append(angle)
        midpoints.append(((x1+x2)/2, (y1+y2)/2))
    angles = np.array(angles)
    midpoints = np.array(midpoints)

    clusters = []
    visited = [False] * len(lines)
    for i in range(len(lines)):
        if visited[i]:
            continue
        cluster = [i]
        visited[i] = True
        # 简单的近邻搜索
        for j in range(i+1, len(lines)):
            if visited[j]:
                continue
            # 角度差（考虑180度周期性，车道线方向一般接近）
            diff_angle = abs(angles[i] - angles[j])
            diff_angle = min(diff_angle, 180.0 - diff_angle)
            # 中点距离
            dist = np.linalg.norm(midpoints[i] - midpoints[j])
            if diff_angle < angle_thresh and dist < dist_thresh:
                cluster.append(j)
                visited[j] = True
        # 计算该聚类的代表线段：取所有线段端点的平均方向，并取最远的两个点作为新端点
        cluster_lines = lines[cluster]  # (k,4)
        # 将所有点收集起来做 PCA 拟合直线
        points = np.vstack([cluster_lines[:,:2], cluster_lines[:,2:]])  # (2k,2)
        # 使用 cv2.fitLine 或简单主成分分析
        [vx,vy,x0,y0] = cv2.fitLine(points, cv2.DIST_L2, 0, 0.01, 0.01)
        # 根据方向获取投影最远两点作为新线段 (x1,y1,x2,y2)
        # 简化：使用最小/最大投影坐标
        t = np.dot(points - (x0,y0), (vx,vy))
        t_min, t_max = np.min(t), np.max(t)
        p1 = (x0 + vx*t_min).flatten()
        p2 = (x0 + vx*t_max).flatten()
        clusters.append( (int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1])) )
    return clusters
```

在获取 `lines = cv2.HoughLinesP(... , lines)` 之后，在斜率筛选之前调用：

```python
# 原代码：lines = cv2.HoughLinesP(edges, ...)
# 新增聚类
clustered_lines = cluster_lines(lines, angle_thresh=10, dist_thresh=60)
# 之后的内容用 clustered_lines 替代 lines 进行左右线分类
```

- **如何验证**：运行节点，在中间输出图像上用不同颜色画出 `lines`（原始）和 `clustered_lines`（聚类后），对比观察碎片化情况。在弯道帧查看能否形成连续长线段。定量：记录连续 100 帧中检测到的左右线段数量，聚类后单侧线段数应接近 1 或少数几条，而不是数十段。

### 步骤 3 — 对车道中心偏移进行帧间指数平滑

- **修改文件**：`lane_follower/scripts/lane_detector.py`
- **定位**：计算完 `lane_center` 偏移量（可能是 `offset` 变量）之后，返回或发送该值之前。通常在主循环末尾或 `compute_offset` 函数内。
- **改什么**：添加一个全局变量存储上一帧偏移值，使用指数加权移动平均 (EMA) `filtered_offset = alpha * offset + (1-alpha) * previous_offset`，输出滤波后的值，限制剧烈跳变。
- **参考代码**：

在模块顶部或全局区域添加状态变量：

```python
# 平滑状态
prev_filtered_offset = 0.0
alpha = 0.3  # 平滑系数，越大响应越快，越小越平滑
```

在计算偏移量的位置（假设变量名为 `current_offset`）：

```python
# 原代码： current_offset = ... （像素偏移）
# 新增平滑
global prev_filtered_offset
if prev_filtered_offset is None:
    prev_filtered_offset = current_offset
filtered_offset = alpha * current_offset + (1 - alpha) * prev_filtered_offset
prev_filtered_offset = filtered_offset

# 使用 filtered_offset 取代后续所有 current_offset 的地方（如发布控制指令或绘制）
```

- **如何验证**：回放一段包含转弯或车道线短暂丢失的 rosbag，对比平滑前后输出偏移曲线（可用 `rqt_plot` 或 CSV 绘图）。观察偏移突变是否被抑制，同时正常偏移跟随是否及时。可调整 `alpha` 后重新测试，找到性能与平滑的最佳平衡点。

---

通过以上三个步骤，可在不引入标定和透视变换的前提下，显著改善车道识别的精度与稳定性。建议实施后立即运行第 4 节所述的验证流程，记录指标变化。