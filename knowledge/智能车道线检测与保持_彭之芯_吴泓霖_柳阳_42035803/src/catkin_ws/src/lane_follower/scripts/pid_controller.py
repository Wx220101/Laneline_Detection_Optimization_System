#!/usr/bin/env python3
import threading
import rospy
from lane_follower.msg import LaneDetection
from geometry_msgs.msg import Twist

class PIDController:
    def __init__(self):
        rospy.init_node('pid_controller', anonymous=True)

        rospy.on_shutdown(self.stop_robot)  # 注册关闭回调
        self.publish_interval = 0.5  # 控制发布间隔，单位：秒
        self.last_publish_time = rospy.get_time()
        # PID参数（可通过launch文件动态调整）
        self.Kp = rospy.get_param('~Kp', 0.1)    # 比例系数
        self.Ki = rospy.get_param('~Ki', 0.01)   # 积分系数
        self.Kd = rospy.get_param('~Kd', 0.1)    # 微分系数
        
        # 控制参数
        self.max_speed = rospy.get_param('~max_speed', 0.2)      # 最大线速度(m/s)
        self.max_steering = rospy.get_param('~max_steering', 0.4) # 最大角速度(rad/s)
        self.target_offset = rospy.get_param('~target_offset', 0) # 目标偏移量(像素)
        
        # PID控制变量
        self.integral = 0.0       # 积分项
        self.prev_error = 0.0     # 上一次误差
        self.last_time = rospy.get_time()  # 上次更新时间
        
        # 订阅车道检测消息，发布控制指令
        self.lane_sub = rospy.Subscriber('/lane_detection', LaneDetection, self.lane_callback)
        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        
        self.deadzone = rospy.get_param('~deadzone', 2)  # 死区范围，像素
        self.steering_history = []  # 用于滑动平均滤波
        self.smooth_window = rospy.get_param('~smooth_window', 1)  # 平滑窗口长度
        threading.Thread(target=self.watchdog).start()

        rospy.loginfo("PID Controller initialized with:")
        rospy.loginfo(f"Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}")
        rospy.loginfo(f"Max speed: {self.max_speed} m/s, Max steering: {self.max_steering} rad/s")

    def stop_robot(self):
        """节点关闭时让小车停止"""
        stop_cmd = Twist()
        stop_cmd.linear.x = 0.0
        stop_cmd.angular.z = 0.0
        self.cmd_pub.publish(stop_cmd)
        rospy.loginfo("Robot stopped on shutdown.")

    def watchdog(self):
        rate = rospy.Rate(10)
        while not rospy.is_shutdown():
            if rospy.get_time() - self.last_msg_time > 0.5:  # 超过0.5s没收到新图像
                stop_cmd = Twist()
                stop_cmd.linear.x = 0.0
                stop_cmd.angular.z = 0.0
                self.cmd_pub.publish(stop_cmd)
                rospy.logwarn("No lane detection - stop cmd sent.")
            rate.sleep()

    def lane_callback(self, msg):
        current_time = rospy.get_time()
        # 节流：只每隔publish_interval发布一次
        if current_time - self.last_publish_time < self.publish_interval:
            return  # 跳过本次回调

        self.last_publish_time = current_time
        
        dt = current_time - self.last_time  # 计算时间差
        
        # 计算误差（当前偏移 - 目标偏移）
        error = msg.offset - self.target_offset

        # 1. 死区处理：在一定偏移范围内不做调整
        if abs(error) < self.deadzone:
            error = 0.0

        # PID计算
        self.integral += error * dt
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        self.integral = max(min(self.integral, 100), -100)
        steering = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        steering = max(min(steering, self.max_steering), -self.max_steering)

        # 2. 滑动平均滤波，使转向更平滑
        self.steering_history.append(steering)
        if len(self.steering_history) > self.smooth_window:
            self.steering_history.pop(0)
        smooth_steering = sum(self.steering_history) / len(self.steering_history)

        # 创建并发布控制指令
        cmd = Twist()
        cmd.linear.x = self.max_speed * (1.0 - 0.5 * abs(smooth_steering)/self.max_steering)
        cmd.angular.z = -smooth_steering
        rospy.loginfo(cmd)
        self.cmd_pub.publish(cmd)

        # 更新状态
        self.prev_error = error
        self.last_time = current_time
        rospy.logdebug(f"Error: {error:.2f} | Steering: {steering:.2f} | Smooth: {smooth_steering:.2f} | Speed: {cmd.linear.x:.2f}")

if __name__ == '__main__':
    try:
        controller = PIDController()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass