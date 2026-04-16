
(cl:in-package :asdf)

(defsystem "lane_follower-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils :std_msgs-msg
)
  :components ((:file "_package")
    (:file "LaneDetection" :depends-on ("_package_LaneDetection"))
    (:file "_package_LaneDetection" :depends-on ("_package"))
  ))