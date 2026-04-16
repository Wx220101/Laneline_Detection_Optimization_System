// Auto-generated. Do not edit!

// (in-package lane_follower.msg)


"use strict";

const _serializer = _ros_msg_utils.Serialize;
const _arraySerializer = _serializer.Array;
const _deserializer = _ros_msg_utils.Deserialize;
const _arrayDeserializer = _deserializer.Array;
const _finder = _ros_msg_utils.Find;
const _getByteLength = _ros_msg_utils.getByteLength;
let std_msgs = _finder('std_msgs');

//-----------------------------------------------------------

class LaneDetection {
  constructor(initObj={}) {
    if (initObj === null) {
      // initObj === null is a special case for deserialization where we don't initialize fields
      this.header = null;
      this.offset = null;
      this.left_lane_detected = null;
      this.right_lane_detected = null;
    }
    else {
      if (initObj.hasOwnProperty('header')) {
        this.header = initObj.header
      }
      else {
        this.header = new std_msgs.msg.Header();
      }
      if (initObj.hasOwnProperty('offset')) {
        this.offset = initObj.offset
      }
      else {
        this.offset = 0.0;
      }
      if (initObj.hasOwnProperty('left_lane_detected')) {
        this.left_lane_detected = initObj.left_lane_detected
      }
      else {
        this.left_lane_detected = false;
      }
      if (initObj.hasOwnProperty('right_lane_detected')) {
        this.right_lane_detected = initObj.right_lane_detected
      }
      else {
        this.right_lane_detected = false;
      }
    }
  }

  static serialize(obj, buffer, bufferOffset) {
    // Serializes a message object of type LaneDetection
    // Serialize message field [header]
    bufferOffset = std_msgs.msg.Header.serialize(obj.header, buffer, bufferOffset);
    // Serialize message field [offset]
    bufferOffset = _serializer.float32(obj.offset, buffer, bufferOffset);
    // Serialize message field [left_lane_detected]
    bufferOffset = _serializer.bool(obj.left_lane_detected, buffer, bufferOffset);
    // Serialize message field [right_lane_detected]
    bufferOffset = _serializer.bool(obj.right_lane_detected, buffer, bufferOffset);
    return bufferOffset;
  }

  static deserialize(buffer, bufferOffset=[0]) {
    //deserializes a message object of type LaneDetection
    let len;
    let data = new LaneDetection(null);
    // Deserialize message field [header]
    data.header = std_msgs.msg.Header.deserialize(buffer, bufferOffset);
    // Deserialize message field [offset]
    data.offset = _deserializer.float32(buffer, bufferOffset);
    // Deserialize message field [left_lane_detected]
    data.left_lane_detected = _deserializer.bool(buffer, bufferOffset);
    // Deserialize message field [right_lane_detected]
    data.right_lane_detected = _deserializer.bool(buffer, bufferOffset);
    return data;
  }

  static getMessageSize(object) {
    let length = 0;
    length += std_msgs.msg.Header.getMessageSize(object.header);
    return length + 6;
  }

  static datatype() {
    // Returns string type for a message object
    return 'lane_follower/LaneDetection';
  }

  static md5sum() {
    //Returns md5sum for a message object
    return 'a91f919b9ab61293532f56a60209641d';
  }

  static messageDefinition() {
    // Returns full string definition for message
    return `
    Header header
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
    
    `;
  }

  static Resolve(msg) {
    // deep-construct a valid message object instance of whatever was passed in
    if (typeof msg !== 'object' || msg === null) {
      msg = {};
    }
    const resolved = new LaneDetection(null);
    if (msg.header !== undefined) {
      resolved.header = std_msgs.msg.Header.Resolve(msg.header)
    }
    else {
      resolved.header = new std_msgs.msg.Header()
    }

    if (msg.offset !== undefined) {
      resolved.offset = msg.offset;
    }
    else {
      resolved.offset = 0.0
    }

    if (msg.left_lane_detected !== undefined) {
      resolved.left_lane_detected = msg.left_lane_detected;
    }
    else {
      resolved.left_lane_detected = false
    }

    if (msg.right_lane_detected !== undefined) {
      resolved.right_lane_detected = msg.right_lane_detected;
    }
    else {
      resolved.right_lane_detected = false
    }

    return resolved;
    }
};

module.exports = LaneDetection;
