import sys
from PyQt5.QtWidgets import QApplication

import system_ops
from gui import FarmGUI

if __name__ == "__main__":
    # 配置底部的标识，便于在Windows任务栏统一图标
    system_ops.set_app_model_id("ChenFeng.NikkiFarmhelper.v1.8")
    
    # 强制让程序感知高清DPI屏幕缩放
    system_ops.set_dpi_awareness()
    
    app = QApplication(sys.argv)
    window = FarmGUI()
    window.show()
    sys.exit(app.exec_())
