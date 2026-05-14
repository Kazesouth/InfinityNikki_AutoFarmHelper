import os
import time
import random
import traceback
from datetime import datetime, timedelta

import cv2
import numpy as np
import pyautogui
import pydirectinput
from PyQt5.QtCore import QThread, pyqtSignal

import config_manager
import inputs
import system_ops

class WorkerStoppedException(Exception):
    pass

class FarmWorker(QThread):
    log_signal = pyqtSignal(str, str) 
    finished_signal = pyqtSignal()

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = True
        self.last_match_val = 0.0 
        self.cfg = config_manager.load_and_validate_config(self.log)

    def log(self, text, color="black"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        if color == "darkorange":
            color = "#FF6347"
        self.log_signal.emit(f"[{timestamp}] {text}", color)
        try:
            with open("farm_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {text}\n")
        except: pass

    def get_img_paths(self, key):
        return config_manager.get_img_paths(self.cfg, key)

    def get_random_time(self, key_or_range):
        if isinstance(key_or_range, str):
            r = self.cfg['ACTION_TIMINGS'].get(key_or_range, [0.5, 1.0])
            return random.uniform(r[0], r[1])
        elif isinstance(key_or_range, (list, tuple)) and len(key_or_range) == 2:
            return random.uniform(key_or_range[0], key_or_range[1])
        elif isinstance(key_or_range, (int, float)):
            return random.uniform(key_or_range * 0.9, key_or_range * 1.1)
        return 0.5

    def random_sleep(self, key_or_range):
        duration = self.get_random_time(key_or_range)
        self.smart_sleep(duration)

    def check_stop(self):
        if not self.is_running:
            raise WorkerStoppedException()

    def smart_sleep(self, duration):
        end_time = time.time() + duration
        while time.time() < end_time:
            self.check_stop()
            sleep_chunk = min(0.1, end_time - time.time())
            if sleep_chunk > 0:
                time.sleep(sleep_chunk)

    def force_screen_on(self):
        self.log(">>> 尝试点亮屏幕 <<<", "blue")
        system_ops.force_screen_on()

    def api_sleep_and_wake(self, seconds_to_sleep):
        system_ops.api_sleep_and_wake(
            seconds_to_sleep, 
            self.settings['enable_sleep'], 
            self.log, 
            lambda: self.is_running, 
            self.check_stop, 
            self.smart_sleep
        )

    def wait_if_near_daily_reset(self):
        now = datetime.now()
        if now.hour == 3 and now.minute >= 55:
            target_time = now.replace(hour=4, minute=0, second=2, microsecond=0)
            wait_seconds = (target_time - now).total_seconds()
            
            self.log(f"当前时间接近游戏日刷新时间(04:00)，为防止月卡弹窗打断种植流程，息屏等待 {wait_seconds:.0f} 秒...", "darkorange")
            time.sleep(2)
            system_ops.turn_off_screen()
            self.smart_sleep(wait_seconds)
            self.force_screen_on()
            self.log("时间已过 04:00，继续进入游戏流程...", "green")

    def robust_click(self, x, y, is_double=False):
        inputs.robust_click(x, y, is_double)

    def match_image(self, template_key, confidence=None):
        self.check_stop()
        if confidence is None:
            confidence = self.cfg.get('CHECK_CONFIDENCE_THRESHOLD', 0.7)
            
        target_list = self.get_img_paths(template_key)
        
        try:
            screenshot = pyautogui.screenshot()
            scr_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            for img_path in target_list:
                if not os.path.exists(img_path): continue
                tpl_img = cv2.imread(img_path)
                if tpl_img is None: continue
                
                result = cv2.matchTemplate(scr_img, tpl_img, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    self.last_match_val = max_val
                    return True
        except Exception as e:
            self.log(f"识别出错: {e}", "red")
        return False

    def click_image(self, template_key, retries=3, wait_time_key="sleep_medium", is_double=False):
        confidence = self.cfg.get('CLICK_CONFIDENCE_THRESHOLD', 0.6)
        target_list = self.get_img_paths(template_key)
        
        for _ in range(retries):
            self.check_stop() 
            found = False
            
            try:
                screenshot = pyautogui.screenshot()
                scr_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                
                for img_path in target_list:
                    if not os.path.exists(img_path): continue
                    tpl_img = cv2.imread(img_path)
                    if tpl_img is None: continue
                    
                    result = cv2.matchTemplate(scr_img, tpl_img, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val >= confidence:
                        self.last_match_val = max_val
                        h, w = tpl_img.shape[:2]
                        cx = max_loc[0] + w // 2
                        cy = max_loc[1] + h // 2
                        
                        self.robust_click(cx, cy, is_double=is_double)
                        self.random_sleep(wait_time_key)
                        found = True
                        break
            except: pass
            
            if found: return True
            self.random_sleep("sleep_medium") 
        return False

    def enter_game_process(self):
        self.wait_if_near_daily_reset()
        self.log("正在寻找游戏启动器窗口...", "black")
        
        start_t = time.time()
        launcher_found = False
        while time.time() - start_t < 20: 
            self.check_stop()
            if self.match_image("launcher_window"):
                self.log(f"已找到游戏启动器窗口。(相似度: {self.last_match_val:.2f})", "green")
                launcher_found = True
                break
            if self.match_image("launcher_start", confidence=self.cfg['LAUNCHER_CONFIDENCE']):
                self.log(f"直接找到了【启动游戏】按钮。(相似度: {self.last_match_val:.2f})", "green")
                launcher_found = True
                break
            self.random_sleep("sleep_medium")
        
        if not launcher_found:
            self.log("未找到启动器窗口，尝试直接寻找按钮...", "darkorange")

        self.log("正在识别【启动游戏】按钮并点击...", "black")
        while not self.click_image("launcher_start", retries=1, wait_time_key="sleep_short"):
            self.check_stop()
            self.random_sleep("sleep_short")
            
        wait_click_again = random.uniform(0.8, 1.2)
        self.log(f"已点击【启动游戏】按钮，{wait_click_again:.1f}秒后再次点击以确保生效。", "green")
        self.smart_sleep(wait_click_again)
        self.click_image("launcher_start", wait_time_key="sleep_short")
        
        for _ in range(2):
            pydirectinput.click()
            self.random_sleep("sleep_short")
        
        self.log("正在等待游戏启动 (Logo检测)...", "black")
        start_t = time.time()
        logo_found = False
        enter_early = False
        while time.time() - start_t < 60:
            self.check_stop()
            if self.match_image("game_logo", confidence=0.6):
                self.log(f"已识别到游戏Logo。(相似度: {self.last_match_val:.2f})", "green")
                logo_found = True
                break
            if self.match_image("click_enter"):
                self.log(f"跳过Logo，直接检测到了入口。(相似度: {self.last_match_val:.2f})", "green")
                enter_early = True
                break
            self.random_sleep("sleep_medium")
            
        if not logo_found and not enter_early: 
            self.log("等待Logo超时，尝试直接寻找入口...", "darkorange")

        self.log("等待【点击进入游戏】界面...", "black")
        start_time = time.time()
        loading_start_time = None
        has_seen_loading = False 
        click_start_time = None
        has_logged_enter_found = False
        has_logged_blind_start = False
        has_logged_loading = False
        has_found_enter_at_least_once = False

        while (time.time() - start_time < self.cfg['TIMEOUT_ENTER_GAME_MAX']):
            self.check_stop()
            
            if self.match_image("ingame_check"):
                self.random_sleep("sleep_long")
                if self.match_image("ingame_check", confidence=0.6):
                    self.log(f">>> 检测到游戏内画面 (二次确认通过)！直接结束进入流程。(相似度: {self.last_match_val:.2f})", "green")
                    break

            if self.match_image("monthly_card"):
                self.log(f"识别到月卡界面，正在点击领取……(相似度: {self.last_match_val:.2f})", "green")
                sw, sh = pyautogui.size()
                cx, cy = sw // 2, sh // 2
                self.robust_click(cx, cy)
                self.smart_sleep(random.uniform(2, 3))
                self.log("再次点击关闭月卡界面……")
                self.robust_click(cx, cy, is_double=True)
                self.random_sleep("sleep_long")
                self.log("月卡领取结束，准备进行下一步。")
                self.smart_sleep(1)
                break

            is_loading = True if has_seen_loading else self.match_image("loading")

            if is_loading:
                has_seen_loading = True
                if loading_start_time is None:
                    loading_start_time = time.time()
                
                if not has_logged_loading:
                    self.log(f"检测到加载画面 (Loading)，正在等待游戏加载... (相似度: {self.last_match_val:.2f})", "blue")
                    has_logged_loading = True
                
                check_time = click_start_time if click_start_time else loading_start_time
                if check_time and (time.time() - check_time > self.cfg['TIMEOUT_LOADING_STUCK']):
                    self.log("警告：进游戏耗时已超过设定，强制跳过等待。", "red")
                    break
                
                self.random_sleep("sleep_medium")
                continue

            sw, sh = pyautogui.size()
            cx, cy = sw // 2, sh // 2
            stop_searching_enter = has_found_enter_at_least_once or ((time.time() - start_time) > 30)

            if stop_searching_enter:
                if not has_found_enter_at_least_once and not has_logged_blind_start:
                    self.log(f"识别【点击进入游戏】界面超时，强制点击屏幕中心……", "darkorange")
                    has_logged_blind_start = True
                
                self.robust_click(cx, cy, is_double=True)
                if click_start_time is None: click_start_time = time.time()
                self.random_sleep("sleep_medium")
            else:
                found = self.click_image("click_enter", retries=1, is_double=True)
                if found:
                    has_found_enter_at_least_once = True
                    if not has_logged_enter_found:
                        self.log(f"识别到【点击进入游戏】界面，正在点击进入游戏…… (相似度: {self.last_match_val:.2f})", "green")
                        has_logged_enter_found = True
                    if click_start_time is None: click_start_time = time.time()
                    self.random_sleep("sleep_long")

            if click_start_time is not None:
                if time.time() - click_start_time > self.cfg['TIMEOUT_LOADING_STUCK']:
                    self.log("警告：进游戏总耗时已超过设定，强制跳过等待。", "red")
                    break
            self.random_sleep("sleep_medium")
        else:
            self.log("警告：进入游戏过程超时，强制尝试进行后续操作。", "darkorange")
        
        self.log("进入流程结束，缓冲 5 秒准备操作...", "black")
        self.smart_sleep(5)

    def wait_for_launcher_restore(self):
        self.log("正在等待启动器界面恢复...", "black")
        start_t = time.time()
        found = False
        while time.time() - start_t < self.cfg['TIMEOUT_LAUNCHER_RESTORE']:
            self.check_stop()
            if self.match_image("launcher_window"):
                self.log(f"已检测到启动器界面。(相似度: {self.last_match_val:.2f})", "green")
                found = True
                break
            self.random_sleep("sleep_medium")
        if not found: self.log("警告：等待启动器恢复超时。", "red")
        self.log("等待 5 秒缓冲...", "black")
        self.smart_sleep(5)

    def move_step_action(self, direction_key, target_wall_key, action_func, step_duration_key, action_wait_key, custom_timeout=None):
        timeout = custom_timeout if custom_timeout else self.cfg['TIMEOUT_FARMING_LOOP']
        
        disp_time = "Random"
        if isinstance(step_duration_key, str) and step_duration_key in self.cfg['ACTION_TIMINGS']:
            r = self.cfg['ACTION_TIMINGS'][step_duration_key]
            disp_time = f"~{(r[0]+r[1])/2:.1f}"

        self.log(f"作业 -> 方向[{direction_key}] 步长[{disp_time}s]", "black")
        start_time = time.time()
        if action_func:
            action_func()
            self.random_sleep(action_wait_key)
        
        timed_out = True
        while (time.time() - start_time < timeout):
            self.check_stop()
            if self.match_image(target_wall_key):
                self.log(f"检测到墙壁，结束。(相似度: {self.last_match_val:.2f})", "green")
                timed_out = False
                break
            
            duration = self.get_random_time(step_duration_key)
            pydirectinput.keyDown(direction_key)
            self.smart_sleep(duration)
            pydirectinput.keyUp(direction_key)
            
            key_step_interval = random.uniform(0.01, 0.1)
            self.smart_sleep(key_step_interval)
            if action_func:
                action_func()
                self.random_sleep(action_wait_key)
        
        if timed_out:
            self.log("单程超时，强制进行下一步", "darkorange")

    def simple_move(self, direction_key, target_wall_key, custom_timeout=None):
        timeout = custom_timeout if custom_timeout else self.cfg['TIMEOUT_FARMING_LOOP']
        self.log(f"归位移动 -> 方向[{direction_key}] (超时限制: {timeout}s)", "black")
        pydirectinput.keyDown(direction_key)
        start_time = time.time()
        timed_out = True
        
        while (time.time() - start_time < timeout):
            self.check_stop()
            if self.match_image(target_wall_key):
                self.log(f"已到达归位点。(相似度: {self.last_match_val:.2f})", "green")
                timed_out = False
                break
            self.random_sleep(0.05)
        pydirectinput.keyUp(direction_key)
        if timed_out:
            self.log("单程超时，强制进行下一步", "darkorange")

    def act_harvest(self): 
        pydirectinput.keyDown('f')
        time.sleep(random.uniform(0.01,0.1))
        pydirectinput.keyUp('f')

    def act_plant(self): 
        pydirectinput.keyDown('r')
        time.sleep(random.uniform(0.005,0.01))
        pydirectinput.keyUp('r')

    def act_water(self):
        pydirectinput.mouseDown(button='right')
        time.sleep(random.uniform(0.1,0.2))
        pydirectinput.mouseUp(button='right')

    def farm_logic(self, only_water=False, crop_choice='2'):
        is_fruit_tree = (crop_choice == '6' or crop_choice == '7')
        plant_timestamp = None 

        if only_water: self.log("=== 开始执行：仅浇水作业 ===", "blue")
        else: self.log(f"=== 开始执行：完整种田流程 (类型: {'果树' if is_fruit_tree else '普通作物'}) ===", "blue")
            
        self.random_sleep("sleep_long")
        if not only_water and not is_fruit_tree and self.match_image("mature"): 
            self.log(f"发现成熟标记。(相似度: {self.last_match_val:.2f})", "green")
        
        if is_fruit_tree:
            self.log("果树模式：调整朝向...", "black")
            pydirectinput.keyDown('s'); self.random_sleep("key_press_short"); pydirectinput.keyUp('s')
            self.random_sleep("sleep_short")
        else:
            self.simple_move('s', "wall_back", custom_timeout=self.cfg['TIMEOUT_HOMING'])
            pydirectinput.keyDown('w'); self.random_sleep("key_press_turn"); pydirectinput.keyUp('w')
            self.random_sleep("sleep_short")

        if only_water:
            self.log("阶段：补充浇水", "black")
            step_key = "move_step_water_fruit" if is_fruit_tree else "move_step_water_normal"
            wait_key = "wait_after_water_fruit" if is_fruit_tree else "wait_after_water_normal"
            self.move_step_action('w', "wall_front", self.act_water, step_key, wait_key)
            self.log("=== 补充浇水完成 ===", "green")
        else:
            if is_fruit_tree:
                self.log("阶段：播种 (R) [S方向 -> Back]", "black")
                plant_timestamp = datetime.now()
                self.move_step_action('s', "wall_back", self.act_plant, "move_step_plant_fruit", "wait_after_plant", custom_timeout=self.cfg['TIMEOUT_FRUIT_PLANT'])
                self.log("到达Back墙，转身 (W)...", "black")
                pydirectinput.keyDown('w'); self.random_sleep("key_press_turn"); pydirectinput.keyUp('w')
                self.random_sleep("sleep_short")
                self.log("阶段：首轮浇水 (右键) [W方向 -> Front]", "black")
                self.move_step_action('w', "wall_front", self.act_water, "move_step_water_fruit", "wait_after_water_fruit", custom_timeout=self.cfg['TIMEOUT_FRUIT_WATER'])
            else:
                self.log("阶段：收获", "black")
                self.move_step_action('w', "wall_front", self.act_harvest, "move_step_harvest", "wait_after_harvest")
                pydirectinput.keyDown('s'); self.random_sleep("key_press_turn"); pydirectinput.keyUp('s')
                self.random_sleep("sleep_short")
                self.log("阶段：播种", "black")
                plant_timestamp = datetime.now()
                self.move_step_action('s', "wall_back", self.act_plant, "move_step_plant_normal", "wait_after_plant", custom_timeout=self.cfg['TIMEOUT_PLANTING'])
                pydirectinput.keyDown('w'); self.random_sleep("key_press_turn"); pydirectinput.keyUp('w')
                self.random_sleep("sleep_short")
                self.log("阶段：首轮浇水", "black")
                self.move_step_action('w', "wall_front", self.act_water, "move_step_water_normal", "wait_after_water_normal")
            self.log("=== 完整作业结束 ===", "green")
        
        return plant_timestamp

    def exit_game_logic(self):
        self.log("执行退出...", "black")
        pydirectinput.keyDown('esc')
        self.random_sleep("key_press_short")
        pydirectinput.keyUp('esc')
        self.random_sleep("sleep_long")
        if self.click_image("exit_icon", retries=3):
            self.log(f"已点击退出。(相似度: {self.last_match_val:.2f})")
            self.random_sleep("move_step_plant_normal")
            if self.click_image("exit_confirm", retries=3):
                self.log(f"已点击确认退出。(相似度: {self.last_match_val:.2f})", "green")
                return
        self.log("强制关闭 (Alt+F4)", "darkorange")
        pydirectinput.keyDown('alt')
        self.random_sleep("key_press_short")
        pydirectinput.keyDown('f4')
        self.random_sleep("key_press_short")
        pydirectinput.keyUp('f4')
        pydirectinput.keyUp('alt')

    def run(self):
        try:
            self.log("================ 脚本启动 ================", "blue")
            if not system_ops.is_admin():
                self.log("错误：请以管理员身份运行！", "red")
                return

            initial_wait_mins = self.settings['initial_wait']
            total_loops = self.settings['loop_count']
            enable_water = self.settings['enable_water']
            water_count = self.settings['water_count']
            final_wait_mins = self.settings['final_wait']
            crop_choice = self.settings['crop_choice']
            enable_ingame_afk = self.settings.get('enable_ingame_afk', False) 

            self.log(f"配置确认: 循环{total_loops}次", "black")
            if enable_ingame_afk:
                 self.log("模式确认: 【游戏内挂机等待成熟】 (不退游戏/不睡眠)", "blue")
            elif self.settings['enable_sleep']:
                 self.log("模式确认: 【电脑睡眠模式】", "blue")
            else:
                 self.log("模式确认: 【仅关闭屏幕】", "blue")

            if enable_water:
                self.log(f"已启用自动浇水: 每次等待期间额外浇水 {water_count} 次", "blue")
            
            self.log("3秒后开始...", "black")
            self.smart_sleep(3)

            if enable_ingame_afk:
                self.enter_game_process()
                for i in range(1, total_loops + 1):
                    self.check_stop()
                    self.log(f"========== 种植循环 {i} / {total_loops} (游戏内挂机) ==========", "blue")
                    self.farm_logic(only_water=False, crop_choice=crop_choice)
                    if i < total_loops:
                        wait_seconds = initial_wait_mins * 60
                        self.log(f"本轮结束，将在游戏内原地等待 {wait_seconds} 秒 ({initial_wait_mins} 分钟)...", "black")
                        self.log("提示：等待期间请勿操作鼠标键盘。", "darkorange")
                        self.smart_sleep(wait_seconds)
                        self.log("等待结束，开始下一轮...", "green")
                    else:
                        self.log("所有循环完成，正在退出游戏...", "green")
                        self.exit_game_logic()
                        self.wait_for_launcher_restore()
            else:
                for i in range(1, total_loops + 1):
                    self.check_stop()
                    self.log(f"========== 种植循环 {i} / {total_loops} ==========", "blue")
                    self.enter_game_process()
                    plant_time = self.farm_logic(only_water=False, crop_choice=crop_choice)
                    self.exit_game_logic()
                    
                    exit_time = datetime.now()
                    base_time = plant_time if plant_time else exit_time
                    if plant_time:
                         self.log(f"计时基准已校准为播种时间: {plant_time.strftime('%H:%M:%S')}", "black")
                    else:
                         self.log(f"未检测到播种操作，使用退出时间作为基准: {exit_time.strftime('%H:%M:%S')}", "darkorange")

                    self.wait_for_launcher_restore()
                    
                    if i == total_loops:
                        self.log("所有种植循环已完成，脚本结束。", "green")
                        break
                    
                    if enable_water and water_count > 0:
                        self.log(f"进入多次浇水挂机模式...", "blue")
                        for w in range(1, water_count + 1):
                            self.check_stop()
                            self.log(f"--- 等待第 {w} / {water_count} 次额外浇水 ---", "black")
                            
                            target_wake_time = base_time + timedelta(minutes=self.cfg['WATER_COOLDOWN_MINUTES'] * w)
                            current_time = datetime.now()
                            
                            if target_wake_time > current_time:
                                seconds_remaining = (target_wake_time - current_time).total_seconds()
                                self.api_sleep_and_wake(seconds_remaining)
                            else:
                                self.log("无需睡眠，时间已过，直接继续...", "darkorange")
                            
                            self.log(f"等待 {self.cfg['NETWORK_RECOVERY_BUFFER']} 秒网络恢复...", "black")
                            self.smart_sleep(self.cfg['NETWORK_RECOVERY_BUFFER'])
                            
                            self.enter_game_process()
                            self.farm_logic(only_water=True, crop_choice=crop_choice)
                            self.exit_game_logic()
                            self.wait_for_launcher_restore()
                            
                    total_elapsed_minutes = (water_count * self.cfg['WATER_COOLDOWN_MINUTES']) + final_wait_mins
                    target_final_wake = base_time + timedelta(minutes=total_elapsed_minutes)
                    
                    current_time = datetime.now()
                    seconds_remaining = 0.0
                    if target_final_wake > current_time:
                        seconds_remaining = (target_final_wake - current_time).total_seconds()
                    
                    self.log(f"准备等待最后 {seconds_remaining:.1f} 秒 ({seconds_remaining/60:.2f} 分钟)...", "blue")
                    
                    if seconds_remaining > 0:
                        self.api_sleep_and_wake(seconds_remaining)
                    else:
                        self.log("无需睡眠，时间已过，直接继续...", "darkorange")
                    
                    self.log(f"等待 {self.cfg['NETWORK_RECOVERY_BUFFER']} 秒网络/系统恢复...", "black")
                    self.smart_sleep(self.cfg['NETWORK_RECOVERY_BUFFER'])
                    self.log("作物已完全成熟，开始下一轮...", "green")

        except WorkerStoppedException:
            self.log(">>> 用户手动停止运行 <<<", "red")
        except Exception as e:
            self.log(f"!!! 发生致命错误 !!! {e}", "red")
            self.log(traceback.format_exc(), "red")
        
        self.finished_signal.emit()
    
    def stop(self):
        self.is_running = False