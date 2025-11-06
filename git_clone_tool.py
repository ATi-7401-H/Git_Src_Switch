import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import platform
import subprocess
import sys
import os
import threading
import urllib.request
import urllib.error
import re

class GitCloneGUI:
    def __init__(self, root):
        # 初始化GUI主窗口
        self.root = root
        self.root.title("Git 克隆工具")  # 设置窗口标题
        self.root.geometry("1500x800")   # 设置窗口大小
        
        # 系统信息
        self.system_info = self.detect_system()  # 检测系统信息
        
        # 创建界面
        self.create_widgets()  # 创建GUI控件
        
        # 检查Git和依赖
        self.check_dependencies()  # 检查并安装必要的依赖
    
    def detect_system(self):
        """检测系统信息"""
        system = platform.system()  # 获取操作系统名称
        info = {
            "system": system,
            "version": "",
            "distribution": ""
        }
        
        # 如果是Linux系统
        if system == "Linux":
            try:
                # 尝试读取/etc/os-release文件获取发行版信息
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    # 使用正则表达式提取版本ID和发行版名称
                    version_match = re.search(r'VERSION_ID="([\d.]+)"', content)
                    name_match = re.search(r'NAME="([^"]+)"', content)
                    
                    # 如果找到发行版名称，则保存
                    if name_match:
                        info["distribution"] = name_match.group(1)
                    # 如果找到版本号，则保存
                    if version_match:
                        info["version"] = version_match.group(1)
                        
            except Exception as e:
                # 如果读取失败，打印错误信息
                print(f"读取系统信息失败: {e}")
                info["distribution"] = "Linux (未知发行版)"
        
        # 如果是Windows系统
        elif system == "Windows":
            info["version"] = platform.version()  # 获取Windows版本
            info["distribution"] = "Windows"  # 设置发行版为Windows
        
        return info  # 返回系统信息字典
    
    def check_dependencies(self):
        """检查并安装Git和依赖"""
        # 在新线程中执行依赖安装，避免阻塞GUI
        threading.Thread(target=self._install_dependencies, daemon=True).start()
    
    def _install_dependencies(self):
        """安装依赖的内部实现"""
        system_info = self.system_info
        
        # 更新系统信息显示
        info_text = f"系统: {system_info['distribution']} {system_info['version']}"
        self.info_label.config(text=info_text)
        
        # 检查Git是否安装
        git_installed = self._check_git_installed()
        
        # 如果Git未安装，则进行安装
        if not git_installed:
            self.log("Git未安装，开始安装...")
            
            # 根据系统类型调用不同的安装方法
            if system_info["system"] == "Linux":
                self._install_linux_dependencies()
            elif system_info["system"] == "Windows":
                self._install_windows_dependencies()
        else:
            self.log("Git已安装")  # Git已安装，记录日志
    
    def _check_git_installed(self):
        """检查Git是否安装"""
        try:
            # 运行git --version命令检查Git是否安装
            subprocess.run(["git", "--version"], check=True, 
                         capture_output=True, timeout=10)
            return True  # 命令成功执行，返回True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False  # 命令执行失败，返回False
    
    def _install_linux_dependencies(self):
        """在Linux系统安装依赖"""
        try:
            # 更新包管理器
            subprocess.run(["sudo", "apt", "update"], check=True, timeout=60)
            # 安装Git
            subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True, timeout=120)
            self.log("Git安装成功")  # 安装成功，记录日志
        except subprocess.TimeoutExpired:
            # 安装超时，尝试更换软件源
            self.log("安装超时，尝试更换源...")
            self._change_ubuntu_source()
        except subprocess.CalledProcessError as e:
            # 安装过程出错，尝试更换软件源
            self.log(f"安装失败: {e}")
            self.log("尝试更换源后重新安装...")
            self._change_ubuntu_source()
    
    def _install_windows_dependencies(self):
        """在Windows系统安装Git"""
        try:
            # 尝试使用winget包管理器安装Git
            subprocess.run(["winget", "install", "--id=Git.Git", "-e"], 
                         check=True, timeout=300)
            self.log("Git安装成功")  # 安装成功，记录日志
        except (subprocess.CalledProcessError, FileNotFoundError):
            # winget安装失败，提示用户手动安装
            self.log("请手动下载并安装Git: https://git-scm.com/download/win")
    
    def _change_ubuntu_source(self):
        """更换Ubuntu源"""
        version = self.system_info["version"]  # 获取系统版本
        sources = self._get_ubuntu_sources(version)  # 获取可用的软件源列表
        
        # 遍历所有可用的软件源
        for source_name, source_url in sources.items():
            try:
                self.log(f"尝试使用 {source_name} 源...")
                # 测试并设置软件源
                self._test_and_set_source(source_url, version)
                # 重新尝试安装Git
                subprocess.run(["sudo", "apt", "update"], check=True, timeout=60)
                subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True, timeout=120)
                self.log("Git安装成功")  # 安装成功，记录日志
                return  # 安装成功，退出函数
            except Exception as e:
                # 当前软件源失败，尝试下一个
                self.log(f"{source_name} 源失败: {e}")
                continue
        
        # 所有软件源都尝试失败
        self.log("所有源都尝试失败，请检查网络连接")
    
    def _get_ubuntu_sources(self, version):
        """获取对应版本的Ubuntu源"""
        # 定义常用的Ubuntu软件镜像源
        base_sources = {
            "清华源": "https://mirrors.tuna.tsinghua.edu.cn/ubuntu/",
            "阿里云": "https://mirrors.aliyun.com/ubuntu/",
            "华为云": "https://mirrors.huaweicloud.com/ubuntu/",
            "中科大": "https://mirrors.ustc.edu.cn/ubuntu/",
            "网易": "http://mirrors.163.com/ubuntu/"
        }
        
        return {name: url for name, url in base_sources.items()}  # 返回软件源字典
    
    def _test_and_set_source(self, source_url, version):
        """测试并设置源"""
        try:
            # 测试软件源连接是否可用
            urllib.request.urlopen(f"{source_url}/dists/focal/Release", timeout=10)
            
            # 备份原有的源文件
            subprocess.run(["sudo", "cp", "/etc/apt/sources.list", "/etc/apt/sources.list.backup"], 
                         check=True)
            
            # 生成新的源文件内容
            source_content = f"""deb {source_url} {version} main restricted universe multiverse
deb {source_url} {version}-updates main restricted universe multiverse
deb {source_url} {version}-backports main restricted universe multiverse
deb {source_url} {version}-security main restricted universe multiverse"""
            
            # 将新的源文件内容写入临时文件
            with open("/tmp/sources.list", "w") as f:
                f.write(source_content)
            
            # 用新的源文件替换系统源文件
            subprocess.run(["sudo", "cp", "/tmp/sources.list", "/etc/apt/sources.list"], 
                         check=True)
            
        except Exception as e:
            # 设置软件源过程中出错，抛出异常
            raise e
    
    def create_widgets(self):
        """创建界面控件"""
        # 顶部系统信息区域
        info_frame = ttk.LabelFrame(self.root, text="系统信息", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        # 系统信息标签
        self.info_label = ttk.Label(info_frame, text="检测系统中...", font=("Arial", 12))
        self.info_label.pack(anchor="w")
        
        # 底部主区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧日志区域
        left_frame = ttk.LabelFrame(main_frame, text="操作日志", padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # 带滚动条的文本区域，用于显示操作日志
        self.log_text = scrolledtext.ScrolledText(left_frame, height=15, width=40)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")  # 初始状态为禁用，只能通过程序写入
        
        # 右侧输入区域
        right_frame = ttk.LabelFrame(main_frame, text="Git克隆", padding=10)
        right_frame.pack(side="right", fill="both", padx=(5, 0))
        
        # 输入框和按钮区域
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill="x", pady=5)
        
        # URL输入标签
        ttk.Label(input_frame, text="Git Clone URL:").pack(anchor="w")
        
        # URL输入框和按钮的容器
        url_frame = ttk.Frame(input_frame)
        url_frame.pack(fill="x", pady=5)
        
        # Git URL输入框，预设"git clone "文本
        self.url_var = tk.StringVar(value="git clone ")
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 克隆按钮
        self.clone_btn = ttk.Button(url_frame, text="克隆", command=self.start_clone)
        self.clone_btn.pack(side="right")
        
        # 进度条，用于显示克隆进度
        self.progress = ttk.Progressbar(right_frame, mode='indeterminate')
        self.progress.pack(fill="x", pady=5)
        
        # 状态显示标签
        self.status_label = ttk.Label(right_frame, text="就绪")
        self.status_label.pack(anchor="w")
    
    def log(self, message):
        """添加日志信息"""
        # 启用文本编辑
        self.log_text.config(state="normal")
        # 在文本末尾添加新日志信息
        self.log_text.insert("end", f"{message}\n")
        # 自动滚动到底部
        self.log_text.see("end")
        # 禁用文本编辑，防止用户修改
        self.log_text.config(state="disabled")
        # 更新GUI界面
        self.root.update()
    
    def start_clone(self):
        """开始克隆"""
        # 从输入框获取URL，并移除预设的"git clone "文本
        url = self.url_var.get().replace("git clone ", "").strip()
        
        # 检查URL是否为空
        if not url:
            messagebox.showerror("错误", "请输入Git仓库URL")
            return
        
        # 禁用克隆按钮，防止重复点击
        self.clone_btn.config(state="disabled")
        # 启动进度条动画
        self.progress.start(10)
        # 更新状态标签
        self.status_label.config(text="克隆中...")
        
        # 在新线程中执行克隆操作，避免阻塞GUI
        threading.Thread(target=self._clone_repo, args=(url,), daemon=True).start()
    
    def _clone_repo(self, url):
        """克隆仓库的内部实现"""
        try:
            # 从URL中提取仓库名称
            repo_name = url.split('/')[-1].replace('.git', '')
            
            # 记录克隆开始日志
            self.log(f"开始克隆: {url}")
            self.log(f"目标目录: {repo_name}")
            
            # 执行git clone命令
            result = subprocess.run(
                ["git", "clone", url],
                capture_output=True,  # 捕获标准输出和错误输出
                text=True,           # 以文本形式返回结果
                timeout=300          # 设置5分钟超时
            )
            
            # 检查命令执行结果
            if result.returncode == 0:
                self.log("克隆成功！")  # 克隆成功，记录日志
                self.status_label.config(text="克隆成功")  # 更新状态标签
            else:
                self.log(f"克隆失败: {result.stderr}")  # 克隆失败，记录错误信息
                self.status_label.config(text="克隆失败")  # 更新状态标签
                # 处理克隆错误
                self._handle_clone_error(url, result.stderr)
                
        except subprocess.TimeoutExpired:
            # 克隆操作超时
            self.log("克隆超时")
            self.status_label.config(text="克隆超时")
        except Exception as e:
            # 其他异常情况
            self.log(f"克隆出错: {e}")
            self.status_label.config(text="出错")
        
        finally:
            # 无论成功或失败，都执行清理操作
            self.progress.stop()  # 停止进度条
            self.clone_btn.config(state="normal")  # 重新启用克隆按钮
    
    def _handle_clone_error(self, url, error_msg):
        """处理克隆错误"""
        self.log("尝试解决克隆问题...")  # 记录错误处理开始
        
        # 检查错误类型
        if "Connection refused" in error_msg or "timeout" in error_msg:
            # 如果是网络连接问题
            if self.system_info["system"] == "Linux":
                self.log("检测到网络连接问题，尝试更换GitHub镜像源...")
                # 尝试使用GitHub镜像源
                self._try_github_mirrors(url)
            else:
                self.log("Windows系统网络问题，请检查网络连接或使用代理")
        else:
            # 其他未知错误
            self.log(f"未知错误: {error_msg}")
    
    def _try_github_mirrors(self, original_url):
        """尝试使用GitHub镜像源"""
        # 常用的GitHub镜像源列表
        mirrors = [
            "https://hub.fastgit.xyz/",
            "https://github.com.cnpmjs.org/",
            "https://gitclone.com/github.com/"
        ]
        
        # 遍历所有镜像源
        for mirror in mirrors:
            # 检查原始URL是否为GitHub仓库
            if "github.com" in original_url:
                # 将原始GitHub URL替换为镜像URL
                mirror_url = original_url.replace("https://github.com/", mirror)
                self.log(f"尝试镜像: {mirror_url}")
                
                try:
                    # 尝试使用镜像源进行克隆
                    result = subprocess.run(
                        ["git", "clone", mirror_url],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    # 检查克隆是否成功
                    if result.returncode == 0:
                        self.log(f"使用镜像 {mirror} 克隆成功！")
                        return  # 克隆成功，退出函数
                    else:
                        self.log(f"镜像 {mirror} 失败")
                        
                except Exception as e:
                    # 当前镜像源克隆失败
                    self.log(f"镜像 {mirror} 出错: {e}")
        
        # 所有镜像源都尝试失败
        self.log("所有镜像都尝试失败")

def main():
    # 检查Python版本，确保版本符合要求
    if sys.version_info < (3, 6):
        print("需要Python 3.6或更高版本")
        return
    
    # 创建Tkinter主窗口
    root = tk.Tk()
    # 创建应用程序实例
    app = GitCloneGUI(root)
    
    # 启动GUI主循环
    root.mainloop()

# 程序入口点
if __name__ == "__main__":
    main()
