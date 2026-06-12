'''
Create Date : 2026/06/12
Author : Ryoya SATO
License : Apach-2.0
'''

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import Bool
from enum import Enum

# --- タスクマネージャーの状態定義 ---

class TaskState( Enum):
    INIT = 0                        # 最初の待機状態
    WAITING_ZX200_DIG = 1          # zx200(ドラグショベル)が掘削を終えるのを待っている状態
    WAITING_IC120_TRANSPORT = 2    # ic120(クローラダンプ)が排土場所に到着するのを待っている状態
    WAITING_IC120_DUMP = 3         # ic120が荷台(ベゼル)を上げ終わるのを待っている状態
    WAITING_IC120_TILT_DOWN = 4    # ic120が荷台を下げ終わるのを待っている状態
    WAITING_IC120_RETURN = 5       # ic120が元の位置に帰ってくるのを待っている状態
    COMPLETE = 6                    # 全ての作業が完了

class TaskManagerNode(Node):
    def __init__(self):
        super().__init__('hackathon_sample_manager_node')

        # --- [1] zx200(ドラグショベル)との通信網 ---
        self.pub_start_dig = self.create_publisher( Bool, '/start_dig', 10)
        self.sub_end_dig = self.create_subscription( Bool, '/end_dig', self.cb_end_dig, 10)

        # --- [2] ic120(クローラダンプ)との通信網 ---
        # [送信]ic120への指示出し
        self.pub_ic120_transport = self.create_publisher( Bool, '/ic120/start_transport', 10)
        self.pub_ic120_tilt_up = self.create_publisher( Bool, '/ic120/tilt_up_cmd', 10)
        self.pub_ic120_tilt_down = self.create_publisher( Bool, '/ic120/tilt_down_cmd', 10)
        self.pub_ic120_return = self.create_publisher( Bool, '/ic120/start_return', 10)

        # [受信]ic120からの報告待ち
        self.sub_ic120_arrived_dump = self.create_subscription( Bool, '/ic120/arrived_dump', self.cb_arrived_dump, 10) 
        self.sub_ic120_dump_done = self.create_subscription( Bool, '/ic120/dump_completed', self.cb_dump_done, 10)
        self.sub_ic120_tilt_down_done = self.create_subscription( Bool, '/ic120/tilt_down_completed', self.cb_tilt_down_done, 10)
        self.sub_ic120_arrived_home = self.create_subscription( Bool, '/ic120/arrived_home',self.cb_arrived_home, 10)

        # 起動直後の状態はINIT(待機中)にセット
        self.current_state = TaskState.INIT

        self.get_logger().info("--- TASK MANAGER READY ---")
        
        # 他のnodeが完全に起動するまで待機
        # ROS2のシステムは起動後, 通信が繋がるまでコンマ数秒のラグが生じる為
        self.timer_start = self.create_timer( 3.0, self.start_sequence)

    # --- シーケンス進行ロジック(イベントコールバック) ---

    def start_sequence(self):
        self.timer_start.cancel()

        if self.current_state == TaskState.INIT:
            self.get_logger().info(">>> Step 1 : Send to zx200 for digging start")
            self.current_state = TaskState.WAITING_ZX200_DIG

            msg = Bool()
            msg.data = True
            self.pub_start_dig.publish( msg)

    def cb_end_dig(self, msg):
        if msg.data and self.current_state == TaskState.WAITING_ZX200_DIG:
            self.get_logger().info("<<< Step 2 : Received end of Digging from zx200")
            self.get_logger().info(">>> Step 3 : Send to ic120 for transpotation")

            self.current_state = TaskState.WAITING_IC120_TRANSPORT
            
            msg_out = Bool()
            msg_out.data = True
            self.pub_ic120_transport.publish( msg_out)

    def cb_arrived_dump(self, msg):
        if msg.data and self.current_state == TaskState.WAITING_IC120_TRANSPORT:
            self.get_logger().info("<<< Step 4 :Received a Notification from ic120")
            self.get_logger().info(">>> Step 4 : Send to ic120 for tilt bezel(up)")

            self.current_state = TaskState.WAITING_IC120_DUMP
            msg_out = Bool()
            msg_out.data = True
            self.pub_ic120_tilt_up.publish(msg_out)

    def cb_dump_done(self, msg):
        if msg.data and self.current_state == TaskState.WAITING_IC120_DUMP:
            self.get_logger().info("<<< Step 5 :Received a Notification from ic120")
            self.get_logger().info(">>> Step 5 : Send to ic120 for tilt bezel(down)")

            self.current_state = TaskState.WAITING_IC120_TILT_DOWN
            msg_out = Bool()
            msg_out.data = True
            self.pub_ic120_tilt_down.publish( msg_out)
            
    def cb_tilt_down_done(self, msg):
        if msg.data and self.current_state == TaskState.WAITING_IC120_TILT_DOWN:
            self.get_logger().info("<<< Step 6 :Received a signal from ic120")
            self.get_logger().info(">>> Step 6 :Send to ic120 for return home position ")

            self.current_state = TaskState.WAITING_IC120_RETURN

            msg_out = Bool()
            msg_out.data = True
            self.pub_ic120_return.publish( msg_out)

    def cb_arrived_home(self, msg):
        if msg.data and self.current_state == TaskState.WAITING_IC120_RETURN:
            self.get_logger().info("<<< Step 7 :Received a Return signal form ic120")
            self.get_logger().info("--- All Task Complete. Finished Systems ---")

            self.current_state = TaskState.COMPLETE

            # 必要に応じて, ここからTaskState.INITに戻しループさせることも可能

def main(args=None):
    rclpy.init(args=args)
    node = TaskManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
