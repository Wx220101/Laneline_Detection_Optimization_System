;; Auto-generated. Do not edit!


(when (boundp 'lane_follower::LaneDetection)
  (if (not (find-package "LANE_FOLLOWER"))
    (make-package "LANE_FOLLOWER"))
  (shadow 'LaneDetection (find-package "LANE_FOLLOWER")))
(unless (find-package "LANE_FOLLOWER::LANEDETECTION")
  (make-package "LANE_FOLLOWER::LANEDETECTION"))

(in-package "ROS")
;;//! \htmlinclude LaneDetection.msg.html
(if (not (find-package "STD_MSGS"))
  (ros::roseus-add-msgs "std_msgs"))


(defclass lane_follower::LaneDetection
  :super ros::object
  :slots (_header _offset _left_lane_detected _right_lane_detected ))

(defmethod lane_follower::LaneDetection
  (:init
   (&key
    ((:header __header) (instance std_msgs::Header :init))
    ((:offset __offset) 0.0)
    ((:left_lane_detected __left_lane_detected) nil)
    ((:right_lane_detected __right_lane_detected) nil)
    )
   (send-super :init)
   (setq _header __header)
   (setq _offset (float __offset))
   (setq _left_lane_detected __left_lane_detected)
   (setq _right_lane_detected __right_lane_detected)
   self)
  (:header
   (&rest __header)
   (if (keywordp (car __header))
       (send* _header __header)
     (progn
       (if __header (setq _header (car __header)))
       _header)))
  (:offset
   (&optional __offset)
   (if __offset (setq _offset __offset)) _offset)
  (:left_lane_detected
   (&optional (__left_lane_detected :null))
   (if (not (eq __left_lane_detected :null)) (setq _left_lane_detected __left_lane_detected)) _left_lane_detected)
  (:right_lane_detected
   (&optional (__right_lane_detected :null))
   (if (not (eq __right_lane_detected :null)) (setq _right_lane_detected __right_lane_detected)) _right_lane_detected)
  (:serialization-length
   ()
   (+
    ;; std_msgs/Header _header
    (send _header :serialization-length)
    ;; float32 _offset
    4
    ;; bool _left_lane_detected
    1
    ;; bool _right_lane_detected
    1
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; std_msgs/Header _header
       (send _header :serialize s)
     ;; float32 _offset
       (sys::poke _offset (send s :buffer) (send s :count) :float) (incf (stream-count s) 4)
     ;; bool _left_lane_detected
       (if _left_lane_detected (write-byte -1 s) (write-byte 0 s))
     ;; bool _right_lane_detected
       (if _right_lane_detected (write-byte -1 s) (write-byte 0 s))
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; std_msgs/Header _header
     (send _header :deserialize buf ptr-) (incf ptr- (send _header :serialization-length))
   ;; float32 _offset
     (setq _offset (sys::peek buf ptr- :float)) (incf ptr- 4)
   ;; bool _left_lane_detected
     (setq _left_lane_detected (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; bool _right_lane_detected
     (setq _right_lane_detected (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;;
   self)
  )

(setf (get lane_follower::LaneDetection :md5sum-) "a91f919b9ab61293532f56a60209641d")
(setf (get lane_follower::LaneDetection :datatype-) "lane_follower/LaneDetection")
(setf (get lane_follower::LaneDetection :definition-)
      "Header header
float32 offset
bool left_lane_detected
bool right_lane_detected
================================================================================
MSG: std_msgs/Header
# Standard metadata for higher-level stamped data types.
# This is generally used to communicate timestamped data 
# in a particular coordinate frame.
# 
# sequence ID: consecutively increasing ID 
uint32 seq
#Two-integer timestamp that is expressed as:
# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')
# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')
# time-handling sugar is provided by the client library
time stamp
#Frame this data is associated with
string frame_id

")



(provide :lane_follower/LaneDetection "a91f919b9ab61293532f56a60209641d")


