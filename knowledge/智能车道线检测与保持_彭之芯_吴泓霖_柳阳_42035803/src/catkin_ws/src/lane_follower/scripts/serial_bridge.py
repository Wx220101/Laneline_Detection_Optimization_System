#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
import serial

class SerialBridge:
    def __init__(self):
        try:
            self.ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            rospy.loginfo("Serial port opened successfully")
        except Exception as e:
            rospy.logerr(f"Failed to open serial port: {e}")
            rospy.signal_shutdown("Serial port error")

        rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)

    def cmd_vel_callback(self, msg):
        min_speed = 0
        x_speed = int(max(abs(msg.linear.x), min_speed) * 1000 * (1 if msg.linear.x >=0 else -1))
        z_speed = int(max(abs(msg.angular.z), min_speed) * 1000 * (1 if msg.angular.z >=0 else -1))

        rospy.loginfo(f"Sending speeds: x={x_speed}, z={z_speed}")

        # 构造协议帧（根据实际协议调整）
        frame = bytearray()
        frame.append(0x7B)  # 帧头
        frame.extend([0x00, 0x00])  # 预留字段
        frame.extend([(x_speed >> 8) & 0xFF, x_speed & 0xFF])  # 线性速度
        frame.extend([0x00, 0x00])  # Y速度（通常为0）
        frame.extend([(z_speed >> 8) & 0xFF, z_speed & 0xFF])  # 角速度
        # BCC校验
        bcc = 0
        for b in frame:
            bcc ^= b
        frame.append(bcc)
        frame.append(0x7D)  # 帧尾

        try:
            self.ser.write(frame)
        except Exception as e:
            rospy.logerr(f"Serial write failed: {e}")

    def run(self):
        rospy.spin()

if __name__ == '__main__':
    rospy.init_node('wheeltec_serial_bridge')
    node = SerialBridge()
    node.run()