#!/usr/bin/env python3
import rospy
import cv2
import time
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraNode:
    def __init__(self):
        rospy.init_node('camera_node', anonymous=True)
        self.bridge = CvBridge()
        self.image_pub = rospy.Publisher('/camera/image_raw', Image, queue_size=10)
        
        # 输入源参数（优先使用视频文件；为空则走摄像头）
        self.video_path = rospy.get_param('~video_path', '')
        self.loop = rospy.get_param('~loop', True)
        self.show = rospy.get_param('~show', False)

        # USB摄像头参数
        self.camera_device = rospy.get_param('~camera_device', '/dev/video0')
        self.frame_width = rospy.get_param('~frame_width', 640)
        self.frame_height = rospy.get_param('~frame_height', 480)
        self.fps = rospy.get_param('~fps', 5)
        
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
        else:
            # 使用V4L2后端打开摄像头
            self.cap = cv2.VideoCapture(self.camera_device, cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            if self.video_path:
                rospy.logerr(f"Cannot open video at {self.video_path}")
            else:
                rospy.logerr(f"Cannot open camera at {self.camera_device}")
            exit(1)
            
        # 设置输入参数（对摄像头更有效；对视频可能被忽略）
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        if not self.video_path:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        
        self.last_time = time.time()
        self.frame_count = 0
    
    def run(self):
        rate = rospy.Rate(self.fps)
        while not rospy.is_shutdown():
            ret, frame = self.cap.read()
            if not ret:
                if self.video_path and self.loop:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                rospy.logerr("Can't receive frame (stream end?). Exiting ...")
                break
                
            try:
                ros_image = self.bridge.cv2_to_imgmsg(frame, "bgr8")
                ros_image.header.stamp = rospy.Time.now()
                self.image_pub.publish(ros_image)

                if self.show:
                    cv2.imshow("Camera Feed", frame)
                    cv2.waitKey(1)  # 必须调用，否则窗口不会更新
            except Exception as e:
                rospy.logerr(e)
                
            self.frame_count += 1
            if self.frame_count % 30 == 0:
                now = time.time()
                fps = 30 / (now - self.last_time)
                print(f"[CameraNode] FPS: {fps:.2f}")
                self.last_time = now

            rate.sleep()
        self.cap.release()
        if self.show:
            cv2.destroyAllWindows()

if __name__ == '__main__':
    try:
        node = CameraNode()
        node.run()
    except rospy.ROSInterruptException:
        pass