#! /usr/bin/env python
# coding:utf-8

import rospy
import tf.transformations as tft

import numpy as np

import kinova_msgs.msg
import kinova_msgs.srv
import std_msgs.msg
import std_srvs.srv
import geometry_msgs.msg

from helpers.gripper_action_client import set_finger_positions
from helpers.position_action_client import position_client, move_to_position
from helpers.transforms import current_robot_pose, publish_tf_quaterion_as_transform, convert_pose, \
    publish_pose_as_transform
from helpers.covariance import generate_cartesian_covariance

MOVING = False  # Flag whether the robot is moving under velocity control.
CURR_Z = 0  # Current end-effector z height.
finger_for_putao = 4400
finger_for_ball = 5000
finger_for_banana = 5600
finger_for_yaokong = 6000
finger_for_zhuizi = 6300
finger_for_initial = 2500
finger_for_daizi = 5800


def robot_wrench_callback(msg):
    # Monitor wrench to cancel movement on collision.
    global MOVING
    if MOVING and msg.wrench.force.z < -2.0:
        MOVING = False
        rospy.logerr('Force Detected. Stopping.')


def robot_position_callback(msg):
    # Monitor robot position.
    global CURR_Z
    CURR_Z = msg.pose.position.z


def move_to_pose(pose):
    # Wrapper for move to position.
    p = pose.position
    o = pose.orientation
    move_to_position([p.x, p.y, p.z], [o.x, o.y, o.z, o.w])


def execute_grasp():
    # Execute a grasp.
    global MOVING
    global CURR_Z
    # global start_force_srv
    # global stop_force_srv

    # Get the positions.
    msg = rospy.wait_for_message('/ggcnn/out/command', std_msgs.msg.Float32MultiArray)
    d = list(msg.data)
    print("d:")
    print(d)
    # Calculate the gripper width.
    grip_width = d[4]
    # Convert width in pixels to mm.
    # 0.07 is distance from end effector (CURR_Z) to camera.
    # 0.1 is approx degrees per pixel for the realsense.
    g_width = 2 * ((CURR_Z + 0.07)) * np.tan(0.1 * grip_width / 2.0 / 180.0 * np.pi) * 1000
    # Convert into motor positions.
    g = min((1 - (min(g_width, 70) / 70)) * (6800 - 4000) + 3700, 5500)
    print("grasp width(max is 7400)%", g / 7400)
    # set_finger_positions([g, g, 0])
    # set_finger_positions([0, 0, 0])
    rospy.sleep(0.5)

    # Pose of the grasp (position only) in the camera frame.

    gp = geometry_msgs.msg.Pose()
    gp.position.x = d[0]
    gp.position.y = d[1]
    gp.position.z = d[2]
    # gp.position.z = 0.1
    gp.orientation.w = 1
    print
    "gp:"
    print
    gp
    # Convert to base frame, add the angle in (ensures planar grasp, camera isn't guaranteed to be perpendicular).
    # 以上设置了Pose中的position部分，将该点通过tf转换至kinova基坐标系中
    # gp_base = convert_pose(gp, '_depth_optical_frame', 'm1n6s300_link_base')
    gp_base = convert_pose(gp, '_depth_optical_frame', 'm1n6s300_link_base')
    finger_single = finger_for_zhuizi
    q = tft.quaternion_from_euler(np.pi, 0, d[3])
    # gp_base.position.x +=
    gp_base.orientation.x = q[0]
    gp_base.orientation.y = q[1]
    gp_base.orientation.z = q[2]
    gp_base.orientation.w = q[3]
    gp_base.position.z = 0.08 # 根据抓取物体调整高度，一般0.02,稍微高点的选0.03,比较小的选择0.015

    # gp_base.position.x += 0.05
    # # gp_base.position.y -= 0.01
    # gp_base.position.z = 0.030
    # # initial
    # gp_base.orientation.x = 0.991159796715
    # gp_base.orientation.y = 0.132007777691
    # gp_base.orientation.z = 0.00999951455742
    # gp_base.orientation.w = 0.00872546527535

    print
    "gp_base"
    print
    gp_base
    # 紧接着处理orientation部分，旋转部分采用四元数表示，默认是xyz旋转，即绕x轴旋转180度，旋转后的y轴不变动，旋转之后的z轴旋转ang（由netword推理得到，与论文一致）角度
    q = tft.quaternion_from_euler(np.pi, 0, d[3])
    # gp_base.orientation.x = q[0]
    # gp_base.orientation.y = q[1]
    # gp_base.orientation.z = q[2]
    # gp_base.orientation.w = gp_base.orientation.w

    publish_pose_as_transform(gp_base, 'm1n6s300_link_base', 'G', 0.5)

    # Offset for initial pose.
    initial_offset = 0.20
    # gp_base.position.z += initial_offset
    # gp_base.position.z = 0.30

    # Disable force control, makes the robot more accurate.
    # stop_force_srv.call(kinova_msgs.srv.StopRequest())

    move_to_pose(gp_base)
    # rospy.sleep(0.1)

    # Start force control, helps prevent bad collisions.
    # start_force_srv.call(kinova_msgs.srv.StartRequest())

    rospy.sleep(0.5)

    # Reset the position
    # gp_base.position.z -= initial_offset

    # Flag to check for collisions.
    # MOVING = True

    # Generate a nonlinearity for the controller.
    # cart_cov = generate_cartesian_covariance(0)

    # Move straight down under velocity control.
    # velo_pub = rospy.Publisher('/m1n6s300_driver/in/cartesian_velocity', kinova_msgs.msg.PoseVelocity, queue_size=1)
    # while MOVING and CURR_Z - 0.02 > gp_base.position.z:
    #     dz = gp_base.position.z - CURR_Z - 0.03   # Offset by a few cm for the fingertips.
    #     MAX_VELO_Z = 0.08
    #     dz = max(min(dz, MAX_VELO_Z), -1.0*MAX_VELO_Z)
    #
    #     v = np.array([0, 0, dz])
    #     vc = list(np.dot(v, cart_cov)) + [0, 0, 0]
    #     velo_pub.publish(kinova_msgs.msg.PoseVelocity(*vc))
    #     rospy.sleep(1/100.0)
    # MOVING = False

    # close the fingers.
    # rospy.sleep(0.1)
    print
    "prepare to open finger"
    set_finger_positions([finger_single, finger_single, finger_single])
    # set_finger_positions([g + 800, g + 750, 0])
    rospy.sleep(0.5)

    # Move back up to initial position.
    # gp_base.position.z += initial_offset
    # gp_base.orientation.x = 1
    # gp_base.orientation.y = 0
    # gp_base.orientation.z = 0
    # gp_base.orientation.w = 0
    # move_to_pose(gp_base)

    move_to_position([0.06517, -0.3191, 0.25], [0.9906, 0.1352, 0.01117, 0.01214])
    move_to_position([0.39347, -0.0907, 0.19], [-0.771, -0.636, -0.0104, 0.00159])
    set_finger_positions([1000, 1000, 1000])  # open finger
    rospy.sleep(1)
    # move_to_position([0.06517, -0.3191, 0.25], [0.9906, 0.1352, 0.01117, 0.01214])
    # move_to_position([0.115523576736, -0.249132305384, 0.266888409853], [-0.985, 0.171, 0.003, 0.005])
    move_to_position([0.115708738565, -0.248527735472, 0.267576545477], [-0.982, 0.169, -0.079, 0.023])
    # stop_force_srv.call(kinova_msgs.srv.StopRequest())

    return


if __name__ == '__main__':
    rospy.init_node('ggcnn_open_loop_grasp')

    # Robot Monitors.
    wrench_sub = rospy.Subscriber('/m1n6s300_driver/out/tool_wrench', geometry_msgs.msg.WrenchStamped,
                                  robot_wrench_callback, queue_size=1)
    position_sub = rospy.Subscriber('/m1n6s300_driver/out/tool_pose', geometry_msgs.msg.PoseStamped,
                                    robot_position_callback, queue_size=1)

    # https://github.com/dougsm/rosbag_recording_services
    # start_record_srv = rospy.ServiceProxy('/data_recording/start_recording', std_srvs.srv.Trigger)
    # stop_record_srv = rospy.ServiceProxy('/data_recording/stop_recording', std_srvs.srv.Trigger)

    # Enable/disable force control.
    # start_force_srv = rospy.ServiceProxy('/m1n6s300_driver/in/start_force_control', kinova_msgs.srv.Start)
    # stop_force_srv = rospy.ServiceProxy('/m1n6s300_driver/in/stop_force_control', kinova_msgs.srv.Stop)

    # Home position.
    print
    "wait here"
    # move_to_position([0.1, -0.38, 0.25], [0.99, 0, 0, np.sqrt(1-0.99**2)])
    # move_to_position([0.115523576736, -0.249132305384, 0.266888409853], [-0.985, 0.171, 0.003, 0.005])
    move_to_position([0.115708738565, -0.248527735472, 0.267576545477], [-0.982, 0.169, -0.079, 0.023])
    # 初始点  水平位置
    print
    "move to init position finished"
    while not rospy.is_shutdown():
        rospy.sleep(0.5)
        finger = [1000, 1000, 1000]
        set_finger_positions(finger)
        rospy.sleep(0.5)

        raw_input('Press Enter to Start.')
        print
        "here starting"
        # start_record_srv(std_srvs.srv.TriggerRequest())
        rospy.sleep(0.5)
        execute_grasp()  # 走这个函数，上边的抓取程序
        # move_to_position([0, -0.38, 0.25], [0.99, 0, 0, np.sqrt(1-0.99**2)])
        # move_to_position([0.06517, -0.3191, 0.25], [0.9906, 0.1352, 0.01117, 0.01214])

        rospy.sleep(0.5)
        # stop_record_srv(std_srvs.srv.TriggerRequest())
        finger = [1000, 1000, 1000]
        set_finger_positions(finger)  # 最后使其夹爪回到非全开状态

        raw_input('Press Enter to Complete')

