#!/usr/bin/env python3
import rospy
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from lane_follower.msg import LaneDetection
import numpy.polynomial.polynomial as poly
import time

class LaneDetector:
    def __init__(self):
        rospy.init_node('lane_detector', anonymous=True)
        self.bridge = CvBridge()
        
        # 参数
        self.lower_yellow = np.array([20, 100, 100])
        self.upper_yellow = np.array([30, 255, 255])
        self.lower_white = np.array([0, 0, 200])
        self.upper_white = np.array([180, 30, 255])
        self.lower_black = np.array([0, 0, 0])
        self.upper_black = np.array([180, 255, 60])
        
        # ROI参数
        self.roi_height = rospy.get_param('~roi_height', 0.6)
        self.roi_width = rospy.get_param('~roi_width', 0.8)
        
        self.image_sub = rospy.Subscriber('/camera/image_raw', Image, self.image_callback)
        self.lane_pub = rospy.Publisher('/lane_detection', LaneDetection, queue_size=10)
        self.last_time = time.time()
        self.frame_count = 0

        
    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except CvBridgeError as e:
            rospy.logerr(e)
            return
        
        # 1. 预处理：BGR转HSV，分别提取黄色、白色和黑色车道线
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        # mask_yellow = cv2.inRange(hsv, self.lower_yellow, self.upper_yellow)
        # mask_white = cv2.inRange(hsv, self.lower_white, self.upper_white)
        mask_black = cv2.inRange(hsv, self.lower_black, self.upper_black)
        # 合并三种颜色mask
        # mask = cv2.bitwise_or(mask_yellow, mask_white)
        mask = mask_black
        
        # 2. 设置ROI（感兴趣区域），只关注下半部分
        height, width = mask.shape
        roi_top = int(height * (1 - self.roi_height))
        roi_bottom = height
        roi_left = int(width * (1 - self.roi_width) / 2)
        roi_right = width - roi_left
        roi = mask[roi_top:roi_bottom, roi_left:roi_right]
        
        # 3. Canny边缘检测
        edges = cv2.Canny(roi, 50, 150)
        
        # 4. 霍夫直线检测
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=50)
        
        # 5. 过滤左右车道线
        left_points = []
        right_points = []
        left_xs = []
        left_ys = []
        right_xs = []
        right_ys = []
        roi_mid_x = (roi_right - roi_left) // 2
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 == x1:
                    continue  # 跳过垂直线，避免除零
                slope = (y2 - y1) / (x2 - x1)
                if abs(slope) < 0.5:
                    continue  # 跳过近似水平线
                mid_x = (x1 + x2) // 2
                mid_y = (y1 + y2) // 2
                if slope < 0:  # 左车道线
                    left_xs.append(mid_x)
                    left_ys.append(mid_y)
                elif slope > 0:  # 右车道线
                    right_xs.append(mid_x)
                    right_ys.append(mid_y)
        
        # 6. 选择离车辆（图像中心）最近的左右车道线
        mid_x_roi = (roi_right - roi_left) // 2
        left_lane = None
        right_lane = None
        if left_xs:
            # 选取小于中心线且最靠近中心的左车道线
            left_candidates = [x for x in left_xs if x < mid_x_roi]
            if left_candidates:
                left_lane = max(left_candidates)  # 最靠近中心的左车道线
            else:
                left_lane = max(left_xs)  # 没有在中心线左侧的，取最右的左线
        if right_xs:
            # 选取大于中心线且最靠近中心的右车道线
            right_candidates = [x for x in right_xs if x > mid_x_roi]
            if right_candidates:
                right_lane = min(right_candidates)  # 最靠近中心的右车道线
            else:
                right_lane = min(right_xs)  # 没有在中心线右侧的，取最左的右线
        
        # 7. 计算偏移量（以原图中心为基准）
        mid_x = width // 2
        roi_offset_x = roi_left
        car_y = roi.shape[0] - 1  # ROI内底部y
        if left_lane is not None and right_lane is not None:
            lane_center = (left_lane + right_lane) // 2 + roi_offset_x
            offset = lane_center - mid_x
        elif left_lane is not None:
            # 单侧左线，拟合曲线
            if len(left_xs) >= 3:
                # 拟合x=f(y)，y为纵坐标
                coefs = poly.Polynomial.fit(left_ys, left_xs, 2).convert().coef
                # 可视化拟合曲线（在ROI内y范围内画点）
                for y in range(0, roi.shape[0], 5):
                    x = int(coefs[0] + coefs[1]*y + coefs[2]*y**2)
                    cv2.circle(cv_image, (x + roi_left, y + roi_top), 2, (0, 0, 255), -1)
                fit_x = coefs[0] + coefs[1]*car_y + coefs[2]*car_y**2
                offset = (fit_x + roi_offset_x) - mid_x + 100
            else:
                offset = left_lane + roi_offset_x - mid_x + 100
        elif right_lane is not None:
            # 单侧右线，拟合曲线
            if len(right_xs) >= 3:
                coefs = poly.Polynomial.fit(right_ys, right_xs, 2).convert().coef
                fit_x = coefs[0] + coefs[1]*car_y + coefs[2]*car_y**2
                offset = (fit_x + roi_offset_x) - mid_x - 100
            else:
                offset = right_lane + roi_offset_x - mid_x - 100
        else:
            offset = 0
        
        # --- 可视化用 ---
        cv2.rectangle(cv_image, (roi_left, roi_top), (roi_right, roi_bottom), (255, 255, 0), 2)
        cv2.line(cv_image, (cv_image.shape[1]//2, 0), (cv_image.shape[1]//2, cv_image.shape[0]), (255, 0, 255), 1)
        if left_lane is not None:
            lx = left_lane + roi_left
            cv2.line(cv_image, (lx, roi_top), (lx, roi_bottom), (0, 0, 255), 2)
        if right_lane is not None:
            rx = right_lane + roi_left
            cv2.line(cv_image, (rx, roi_top), (rx, roi_bottom), (0, 255, 0), 2)
        if left_lane is not None and right_lane is not None:
            lane_center = (left_lane + right_lane) // 2 + roi_left
            cv2.line(cv_image, (lane_center, roi_top), (lane_center, roi_bottom), (0, 255, 255), 2)
        cv2.imshow("Lane Detection Debug", cv_image)
        cv2.waitKey(1)
        
        # 8. 发布检测结果
        lane_msg = LaneDetection()
        lane_msg.header.stamp = rospy.Time.now()
        lane_msg.offset = offset
        lane_msg.left_lane_detected = left_lane is not None
        lane_msg.right_lane_detected = right_lane is not None
        self.lane_pub.publish(lane_msg)
        self.frame_count += 1
        if self.frame_count %30 == 0:
            now = time.time()
            fps=30/(now-self.last_time)
            print(f"[LaneDetector] Fps: {fps:.2f}")
            self.last_time = now

if __name__ == '__main__':
    try:
        detector = LaneDetector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass