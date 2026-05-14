import ctypes
import time

class LARGE_INTEGER(ctypes.Structure):
    _fields_ = [("QuadPart", ctypes.c_longlong)]

def set_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except AttributeError:
        pass

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def set_app_model_id(app_id):
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except:
        pass

def force_screen_on():
    """唤醒/点亮屏幕"""
    user32 = ctypes.windll.user32
    try:
        user32.SetCursorPos(100, 100)
        time.sleep(0.1)
        user32.SetCursorPos(105, 105)
        user32.keybd_event(0x10, 0, 0, 0)
        user32.keybd_event(0x10, 0, 2, 0)
    except: pass

def turn_off_screen():
    """关闭屏幕"""
    try:
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
    except:
        pass

def api_sleep_and_wake(seconds_to_sleep, enable_sleep, log_callback, is_running_callback, check_stop_callback, smart_sleep_callback):
    """利用 Windows WaitableTimer 机制实现精准休眠唤醒"""
    kernel32 = ctypes.windll.kernel32
    powrprof = ctypes.windll.PowrProf
    
    if not enable_sleep:
        log_callback("睡眠模式未开启，仅关闭屏幕...", "darkorange")
        turn_off_screen()
        smart_sleep_callback(seconds_to_sleep)
        force_screen_on()
        return

    if seconds_to_sleep < 120:
        log_callback(f"睡眠时间太短 ({seconds_to_sleep}s)，直接等待...", "darkorange")
        smart_sleep_callback(seconds_to_sleep)
        return

    log_callback(f"设置硬件唤醒定时器: {seconds_to_sleep:.1f} 秒 ({seconds_to_sleep/60:.2f} 分钟)...", "blue")
    timer_handle = kernel32.CreateWaitableTimerW(None, True, "NuanNuanWakeTimer")
    if not timer_handle:
        log_callback("错误：无法创建唤醒定时器！", "red")
        return

    due_time = LARGE_INTEGER()
    due_time.QuadPart = -1 * int(seconds_to_sleep * 10000000)
    success = kernel32.SetWaitableTimer(timer_handle, ctypes.byref(due_time), 0, None, None, True)

    if not success:
        log_callback("错误：无法激活唤醒定时器", "red")
        kernel32.CloseHandle(timer_handle)
        return

    log_callback(">>> 系统即将进入睡眠 (S3) <<<", "blue")
    log_callback(">>> 10秒后进入睡眠 <<<", "blue")
    smart_sleep_callback(10) 
    
    powrprof.SetSuspendState(0, 0, 0)
    
    while is_running_callback():
        res = kernel32.WaitForSingleObject(timer_handle, 500)
        if res == 0: 
            break
    
    kernel32.CloseHandle(timer_handle)
    check_stop_callback() 
    log_callback(">>> 系统已由定时器唤醒 <<<", "green")
    force_screen_on()