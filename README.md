# 使用方法
## 方法一
使用以下代码将仓库克隆下来：
```
git clone https://github.com/Kazesouth/InfinityNikki_AutoFarmHelper
```
安装requirements.txt中所需的库，然后运行main.py
## 方法二
1.直接下载zip压缩包文件，解压后得到如下文件和文件夹。\
<img width="905" height="228" alt="QQ20260514-224222" src="https://github.com/user-attachments/assets/2d1d870f-b660-406e-b6f3-c5c956c711af" />
\
2.文件夹“imgs”是存放模板图片的，如果默认的图片不合适，你也可以换成自己截图的图片（版本更新时需要将启动器和进入游戏画面的图片都更换掉）。\
图片名称可以改，但不建议改，因为改的话得同时改json5文件里面图片的名称。截图时建议截图的分辨率和游戏分辨率都一致（默认模板图片分辨率为1440\*900，因此需要将游戏窗口改成1440\*900），不然有可能识别不成功。\
3.点击“无限暖暖家园小助手.exe”打开脚本程序，打开后界面是这样的：\
<img width="352" height="832" alt="QQ20260514-223013" src="https://github.com/user-attachments/assets/612d34db-e633-4b5b-b748-1cb991f35230" />\
4.在运行脚本程序之前，需要将家园的田地按照下图摆放（摆放成长条，周围用墙或木板灯障碍物围起来），并调整好视角。\
同时确保已切换种植能力，并持有足够多的种子。\
<img width="1442" height="912" alt="QQ20260514-231042" src="https://github.com/user-attachments/assets/eab562cf-8793-4bcd-bf40-5bebb217b11c" />\
<img width="1442" height="911" alt="QQ20260514-231105" src="https://github.com/user-attachments/assets/b145f0c8-6ce1-409f-b757-f4c4609acd0b" />\
<img width="1442" height="915" alt="QQ20260514-231128" src="https://github.com/user-attachments/assets/c493313e-eec7-4f77-9143-073fac0c6411" />
\
这样摆放↑\
<img width="1442" height="912" alt="QQ20260514-200722" src="https://github.com/user-attachments/assets/b1a285c4-5e99-43e2-a5d2-e75972d5bc53" />
\
调整好初始视角↑\
5.打开游戏启动器置于前台。\
确认配置后就可以开始运行脚本了。\
初次运行会生成json5配置文件（记事本打开）和log日志文件。

## 注意：
1.部分杀毒软件会直接拦截软件或拦截鼠标键盘模拟输入，使用此脚本软件前请关闭杀毒软件或将脚本软件添加至白名单。\
2.【开启睡眠模式】和【仅关闭屏幕模式】需要设置电脑从睡眠中唤醒时无须登录：\
打开**电脑设置→帐户→登录选项→需要登录→选择“从不”**。\
并在控制面板里开启“**允许使用唤醒定时器**”：\
打开**控制面板→系统和安全→电源选项→更改计划设置→更改高级电源设置→找到“睡眠”→允许使用唤醒定时器→（2个选项全部启用）**


# 免责声明 / Disclaimer

## 中文声明

本项目（以下简称“本软件”）是一个基于视觉图像识别与键鼠模拟操作的开源自动化脚本，仅用于**技术学习、交流与研究**，禁止用于任何商业用途或违反游戏规则的行为。

- **技术原理**：本软件仅通过屏幕截图与图像识别判断游戏状态，并模拟键盘、鼠标输入进行操作，**完全不涉及**游戏客户端的内存读写、修改、注入、逆向等任何可能破坏游戏安全性的行为。尽管如此，自动化模拟输入仍有可能被游戏安全系统识别为违规操作。
- **风险提示**：使用本软件可能违反《无限暖暖》游戏的相关服务条款、用户协议或公平游戏政策，可能导致游戏账号被警告、限制、封禁或其他处罚。使用者应充分了解并**自行承担**使用本软件带来的一切风险与后果。
- **责任豁免**：本软件的开发者（本人）不对因使用或滥用本软件造成的任何直接或间接损失负责，包括但不限于游戏账号封禁、虚拟财产损失、计算机系统损坏、数据丢失等。一旦使用本软件，即视为您已**接受全部风险**并同意免除开发者的一切责任。
- **第三方权利**：《无限暖暖》（Infinity Nikki）及相关游戏素材、商标、角色等权益均归**上海叠纸网络科技有限公司**所有。本软件为第三方开源项目，与官方游戏公司无任何关联，也未获得官方授权或背书。
- **合规使用**：请尊重游戏开发者的劳动成果，支持正版游戏。本人**不鼓励**任何违反游戏规则的使用方式，强烈建议仅在游戏官方允许的范围内、或使用离线/私服学习环境运行本软件。

## English Disclaimer

This project (the "Software") is an open-source automation tool based on visual image recognition and keyboard/mouse simulation, intended **solely for technical learning, communication, and research**. Commercial use or any violation of game rules is strictly prohibited.

- **Technical Principle**: The Software only performs screen capture, image recognition, and simulation of keyboard/mouse inputs. It does **NOT** involve any reading, writing, modification, injection, or reverse engineering of the game's memory. Nevertheless, automated input simulation may still be detected by the game's security system as a policy violation.
- **Risk Warning**: Using this Software may violate the Terms of Service, End User License Agreement, or fair play policies of *Infinity Nikki*, and could result in warnings, restrictions, or permanent bans of your game account. All risks and consequences arising from the use of this Software shall be **borne solely by the user**.
- **Limitation of Liability**: The developer(s) and contributors（me） of this Software shall not be held liable for any direct or indirect damages caused by the use or misuse of the Software, including but not limited to game account bans, loss of virtual property, computer system damage, or data loss. By using this Software, you acknowledge that you have **accepted all risks** and agree to release the developer(s) from any liability.
- **Third-Party Rights**: *Infinity Nikki* and all related game materials, trademarks, and characters are the property of **Shanghai Folding Paper Technology Co., Ltd** (叠纸科技). This project is an independent third-party open-source project and is not affiliated with, authorized, or endorsed by the official game company.
- **Compliant Usage**: Please respect the game developers and support the official release. The developer(s) do **not** encourage any use that violates game rules. It is strongly recommended to use this Software only within officially permitted scenarios, or in offline/private server environments for educational purposes.
