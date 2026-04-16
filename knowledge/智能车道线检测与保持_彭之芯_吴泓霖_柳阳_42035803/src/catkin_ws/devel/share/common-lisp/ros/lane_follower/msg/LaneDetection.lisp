; Auto-generated. Do not edit!


(cl:in-package lane_follower-msg)


;//! \htmlinclude LaneDetection.msg.html

(cl:defclass <LaneDetection> (roslisp-msg-protocol:ros-message)
  ((header
    :reader header
    :initarg :header
    :type std_msgs-msg:Header
    :initform (cl:make-instance 'std_msgs-msg:Header))
   (offset
    :reader offset
    :initarg :offset
    :type cl:float
    :initform 0.0)
   (left_lane_detected
    :reader left_lane_detected
    :initarg :left_lane_detected
    :type cl:boolean
    :initform cl:nil)
   (right_lane_detected
    :reader right_lane_detected
    :initarg :right_lane_detected
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass LaneDetection (<LaneDetection>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <LaneDetection>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'LaneDetection)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name lane_follower-msg:<LaneDetection> is deprecated: use lane_follower-msg:LaneDetection instead.")))

(cl:ensure-generic-function 'header-val :lambda-list '(m))
(cl:defmethod header-val ((m <LaneDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader lane_follower-msg:header-val is deprecated.  Use lane_follower-msg:header instead.")
  (header m))

(cl:ensure-generic-function 'offset-val :lambda-list '(m))
(cl:defmethod offset-val ((m <LaneDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader lane_follower-msg:offset-val is deprecated.  Use lane_follower-msg:offset instead.")
  (offset m))

(cl:ensure-generic-function 'left_lane_detected-val :lambda-list '(m))
(cl:defmethod left_lane_detected-val ((m <LaneDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader lane_follower-msg:left_lane_detected-val is deprecated.  Use lane_follower-msg:left_lane_detected instead.")
  (left_lane_detected m))

(cl:ensure-generic-function 'right_lane_detected-val :lambda-list '(m))
(cl:defmethod right_lane_detected-val ((m <LaneDetection>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader lane_follower-msg:right_lane_detected-val is deprecated.  Use lane_follower-msg:right_lane_detected instead.")
  (right_lane_detected m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <LaneDetection>) ostream)
  "Serializes a message object of type '<LaneDetection>"
  (roslisp-msg-protocol:serialize (cl:slot-value msg 'header) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'offset))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'left_lane_detected) 1 0)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'right_lane_detected) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <LaneDetection>) istream)
  "Deserializes a message object of type '<LaneDetection>"
  (roslisp-msg-protocol:deserialize (cl:slot-value msg 'header) istream)
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'offset) (roslisp-utils:decode-single-float-bits bits)))
    (cl:setf (cl:slot-value msg 'left_lane_detected) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:setf (cl:slot-value msg 'right_lane_detected) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<LaneDetection>)))
  "Returns string type for a message object of type '<LaneDetection>"
  "lane_follower/LaneDetection")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'LaneDetection)))
  "Returns string type for a message object of type 'LaneDetection"
  "lane_follower/LaneDetection")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<LaneDetection>)))
  "Returns md5sum for a message object of type '<LaneDetection>"
  "a91f919b9ab61293532f56a60209641d")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'LaneDetection)))
  "Returns md5sum for a message object of type 'LaneDetection"
  "a91f919b9ab61293532f56a60209641d")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<LaneDetection>)))
  "Returns full string definition for message of type '<LaneDetection>"
  (cl:format cl:nil "Header header~%float32 offset~%bool left_lane_detected~%bool right_lane_detected~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'LaneDetection)))
  "Returns full string definition for message of type 'LaneDetection"
  (cl:format cl:nil "Header header~%float32 offset~%bool left_lane_detected~%bool right_lane_detected~%================================================================================~%MSG: std_msgs/Header~%# Standard metadata for higher-level stamped data types.~%# This is generally used to communicate timestamped data ~%# in a particular coordinate frame.~%# ~%# sequence ID: consecutively increasing ID ~%uint32 seq~%#Two-integer timestamp that is expressed as:~%# * stamp.sec: seconds (stamp_secs) since epoch (in Python the variable is called 'secs')~%# * stamp.nsec: nanoseconds since stamp_secs (in Python the variable is called 'nsecs')~%# time-handling sugar is provided by the client library~%time stamp~%#Frame this data is associated with~%string frame_id~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <LaneDetection>))
  (cl:+ 0
     (roslisp-msg-protocol:serialization-length (cl:slot-value msg 'header))
     4
     1
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <LaneDetection>))
  "Converts a ROS message object to a list"
  (cl:list 'LaneDetection
    (cl:cons ':header (header msg))
    (cl:cons ':offset (offset msg))
    (cl:cons ':left_lane_detected (left_lane_detected msg))
    (cl:cons ':right_lane_detected (right_lane_detected msg))
))
