import time
import math
import random
import pyautogui
import pydirectinput

# 默认 PAUSE (建议设置为0，由脚本控制延迟)
pydirectinput.PAUSE = 0 

def _linear_move_steps(x1, y1, x2, y2, step_pixels, sleep_base):
    """辅助函数：分段线性移动"""
    try:
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 1: return
        
        # 根据距离和步长计算需要移动多少次
        steps = int(dist / step_pixels)
        if steps < 1: steps = 1
        
        for i in range(1, steps + 1):
            t = i / steps
            current_x = x1 + (x2 - x1) * t
            current_y = y1 + (y2 - y1) * t
            
            pydirectinput.moveTo(int(current_x), int(current_y))
            
            # 这里的 sleep_base 越小移动越快，random 增加一点不确定性
            if sleep_base > 0:
                time.sleep(sleep_base + random.uniform(0, 0.002))
    except Exception:
        # 辅助移动过程出错（如鼠标无法移动），静默失败，由外层 human_move_to 的异常处理接管
        pass

def human_move_to(x, y):
    """模拟人类操作：快速直线移动到附近 -> 慢速直线定位到目标"""
    try:
        start_x, start_y = pyautogui.position()
        
        # 目标点加入微小随机偏移 (模拟人手很难精确点击同一个像素中心)
        end_x = x + random.randint(-2, 2)
        end_y = y + random.randint(-2, 2)
        
        dist = math.hypot(end_x - start_x, end_y - start_y)
        
        # 如果距离本来就很近 (<150像素)，直接进行一次普通的匀速移动即可
        if dist < 150:
            _linear_move_steps(start_x, start_y, end_x, end_y, step_pixels=100, sleep_base=0.002)
            return

        # 1. 快速逼近阶段 (粗定位)
        ratio = random.uniform(0.75, 0.85)
        
        # 计算中间拐点 (Elbow Point)，加入随机偏差 (±15像素)
        mid_x = start_x + (end_x - start_x) * ratio + random.randint(-15, 15)
        mid_y = start_y + (end_y - start_y) * ratio + random.randint(-15, 15)
        
        # 执行快速移动：步长跨度大(45px/step)，几乎无额外延迟
        _linear_move_steps(start_x, start_y, mid_x, mid_y, step_pixels=200, sleep_base=0.001)
        
        move_interval = random.uniform(0.05, 0.3)
        time.sleep(move_interval)

        # 2. 慢速定位阶段 (精定位)
        _linear_move_steps(mid_x, mid_y, end_x, end_y, step_pixels=100, sleep_base=0.002)
        
    except Exception:
        try:
            pydirectinput.moveTo(x, y)
        except:
            pass

def robust_click(x, y, is_double=False):
    """统一的点击逻辑 (拟人化增强)"""
    # 1. 拟人化移动到目标附近
    human_move_to(x, y)
    
    # 2. 点击前的微小停顿 (确认目标)
    time.sleep(random.uniform(0.1, 0.3))
    
    clicks = 2 if is_double else 1
    for i in range(clicks):
        pydirectinput.mouseDown()
        # 随机按压时长
        time.sleep(random.uniform(0.05, 0.15))
        pydirectinput.mouseUp()
        
        if is_double and i == 0:
            # 双击间隔随机
            time.sleep(random.uniform(0.04, 0.1))
    
    # 3. 点击后的休息
    time.sleep(random.uniform(0.1, 0.3))