import threading
import math
from flask import Flask, render_template, request, jsonify
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

app = Flask(__name__)

class JointPublisherNode(Node):
    def __init__(self):
        super().__init__('joint_web_publisher')
        # Using Float64MultiArray for precise joint targets
        self.publisher_ = self.create_publisher(Float64MultiArray, '/target_joint_states', 10)
        self.get_logger().info('ROS 2 Joint Publisher Node Initialized.')

    def publish_joints_in_radians(self, degrees_list):
        # Convert degrees from web UI into radians for ROS 2 standard
        radians_list = [math.radians(deg) for deg in degrees_list]
        
        msg = Float64MultiArray()
        msg.data = radians_list
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published (Deg): {degrees_list}')
        self.get_logger().info(f'Published (Rad): {[round(r, 4) for r in radians_list]}')

ros_node = None

def ros2_thread():
    global ros_node
    rclpy.init()
    ros_node = JointPublisherNode()
    rclpy.spin(ros_node)
    ros_node.destroy_node()
    rclpy.shutdown()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/publish_joints', methods=['POST'])
def publish_joints():
    data = request.get_json()
    joints_deg = data.get('joints', [])
    
    if len(joints_deg) != 6:
        return jsonify({'status': 'error', 'message': 'Expected exactly 6 joint values'}), 400

    if ros_node:
        ros_node.publish_joints_in_radians(joints_deg)
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'ROS 2 node is down'}), 500

if __name__ == '__main__':
    threading.Thread(target=ros2_thread, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)