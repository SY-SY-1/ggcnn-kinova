# ggcnn-kinova
    基于GG-CNN预测每个像素的抓取质量和姿态，通过机器人仿真软件Gazebo实时观察待抓取物体的抓取点。抓取数据集使用康奈尔数据集以及提花数据集；基于kinova机器人搭建实际抓取环境；进行机械臂的手眼标定（Eye-in-Hand）；基于pybullet平台仿真实现多个目标杂乱环境的单个物体抓取（抓取点抓取，不能识别物体的种类）。
一、平台搭建：
    1、硬件平台搭建：硬件层面主要涉及机器人的驱动，通过机器人的接口程序完成轨迹规划，夹具控制，对RGB-D相机进行标定，获得相机的内参数矩阵，确定像素平面到相机坐标系的转换关系，对手眼系统进行标定，确定相机坐标系和机器人基坐标系的关系，最后对实际的物体抓取过程进行实验，包括单目标场景和多目标场景。抓取系统包括机械臂，末端工具、相机以及上位机四部分。其中机械臂完成系统的轨迹规划，轨迹执行，末端完成物体抓取工作，相机完成感知工作，上位机提供算力和算法支撑。采用Kinova公司mico2六自由度服务机器人，末端移动距离最远至90cm，带有可独立控制的三指末端工具。
    2、系统软件平台搭建
抓取系统软件需要将感知、处理、机器人控制等子系统统一起来，各个环节呈现相互依赖关系，软件结构框图如图，由图可知，抓取系统分为感知，检测，决策，执行四大模块，各个模块之间通过TCP/IP或者ROS话题机制进行消息的传输，通过ROS中的节点机制提供功能模块服务，大致处理流程如下：首先相机采集图像信息保存至本地，通信模块采用TCP/IP协议将图像信息发送至服务器，服务器端采用检测算法获得抓取位姿，采用第四章提出的基于Cascade R-CNN抓取检测算法，服务器端将抓取位姿通过协议传输至上位机，上位机处理得到图像中抓取位姿信息发布于话题物品信息中，然后决策模块对物品信息进行综合判断分析，选择置信度较高的物品信息抓取，通过Kinova机器人ROS接口发布抓取信息，最后机器人完成轨迹执行，并根据一定策略执行抓取。
二、GG-CNN
    基于GG-CNN预测每个像素的抓取质量和姿态，通过机器人仿真软件Gazebo实时观察待抓取物体的抓取点。抓取数据集使用康奈尔数据集以及提花数据集；
ggcnn是一种实时、轻量、可进行扩展物体的闭环抓取、提出抓取检测的新型表示方法：质量点抓取。只以深度图为输入，直接端到端输出，不生成候选框再筛选。
基于深度学习的抓取检测进展迅速，但是几多都是采用为目标识别设计的网络的改进版
    GG-CNN网络的优点：
    （1）不对候选框进行采样，以深度图为输入，采用全卷积神经网络直接端到端输出每个像素上的抓取位姿。
    （2）闭环静态单目标
三、提取抓取点模式
    提取候选抓取框->使用神经网络对候选框排序->得到最优抓取框->运行抓取。
    上述流程为开环控制，主要原因是以前的神经网络参数都为百万级，检测时间数秒。
    该方法使用较小的网络和为每个像素都生成一个抓取位姿来解决耗时长、提取候选框的问题。
四、基于Pybullet的多物体抓取仿真实验
    抓取位姿检测及可视化
    加载出相机、机械臂、抓手和待抓取物体之后，仿真摄像头实时的拍摄待抓取物体图片并渲染出深度图和RGB图。送到已经预训练好的抓取位姿检测网络进行检测，预测出合适的抓取位姿。如图绿色的点为抓取框中心点，红色的线为抓取的宽度和机械臂旋转的角度，从而驱动机械臂到达指定位置实时抓取。
    机器人能够通过识别图像中的物体，预测出合适的抓取位姿，并驱动机械臂到达目标点进行物体的抓取。
    两种常见的机器人仿真平台：基于Pybullet平台和在ROS下基于MoveIt+Gazebo仿真平台。对Pybullet仿真平台进行搭建，搭建之后将预先训练好的网络模型加载，并在Pybullet中制作机器人URDF模型和待抓取的物体模型。最并对图片检测进行可视化分析。        
    检测图    
    ![image](https://user-images.githubusercontent.com/80105687/178273695-d3fcba4f-d34a-4b75-977a-4cc289cfe46c.png)    
    抓取实物图    
    ![image](https://user-images.githubusercontent.com/80105687/178282178-b65b02e0-b595-4ba1-9929-acd442e5d6f4.png)
