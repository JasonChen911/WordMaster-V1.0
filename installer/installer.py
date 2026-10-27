"""
WordMaster Windows Installer — GUI-based, packaged as standalone EXE.
Uses tkinter (bundled with Python) for the GUI.
"""

import os, sys, shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# ── Constants ──
APP_NAME = "WordMaster"
VERSION = "0.1.0"
# Per-user install: no admin required. Install under %LOCALAPPDATA%\Programs.
DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Programs" / APP_NAME
INSTALLER_DIR = Path(__file__).resolve().parent  # directory containing this script
BUNDLE_DIR = INSTALLER_DIR / "bundle"             # bundled files to install




class Installer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} {VERSION} 安装程序")
        self.root.geometry("560x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")

        # Center on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

        self.install_dir = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.create_desktop = tk.BooleanVar(value=True)
        self.create_startmenu = tk.BooleanVar(value=True)
        self.license_accepted = tk.BooleanVar(value=False)
        self.step = 0

        # style
        self.bg = "#f5f5f5"
        self.accent = "#6366f1"
        self.fg = "#1a1a1c"
        self.fg2 = "#6b6b70"

        self.show_welcome()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def heading(self, text):
        tk.Label(self.root, text=text, font=("Microsoft YaHei UI", 16, "bold"),
                 fg=self.fg, bg=self.bg).pack(pady=(24, 4))

    def subtext(self, text):
        tk.Label(self.root, text=text, font=("Microsoft YaHei UI", 9),
                 fg=self.fg2, bg=self.bg, wraplength=480).pack(pady=(0, 12))

    def divider(self):
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=40)

    def btn_primary(self, text, command):
        btn = tk.Button(self.root, text=text, command=command,
                        font=("Microsoft YaHei UI", 10, "bold"),
                        bg=self.accent, fg="white", activebackground="#4f46e5",
                        activeforeground="white", relief="flat", cursor="hand2",
                        padx=32, pady=8, borderwidth=0)
        btn.pack(pady=10)
        return btn

    def btn_secondary(self, text, command):
        btn = tk.Button(self.root, text=text, command=command,
                        font=("Microsoft YaHei UI", 9),
                        bg="#e0e0e0", fg=self.fg, activebackground="#d0d0d0",
                        activeforeground=self.fg, relief="flat", cursor="hand2",
                        padx=24, pady=6, borderwidth=0)
        btn.pack(pady=4)
        return btn

    def show_welcome(self):
        self.clear()
        self.step = 0
        tk.Label(self.root, text="📚", font=("", 48), bg=self.bg).pack(pady=(30, 8))
        self.heading("WordMaster 智能英语学习软件")
        self.subtext("版本 " + VERSION + "  |  基于艾宾浩斯记忆曲线的 AI 辅助学习工具")
        self.divider()
        tk.Label(self.root, text="• 内置 CET4/CET6/IELTS/TOEFL 词库\n• AI 单词解释 + 游戏化学习\n• 艾宾浩斯间隔复习系统",
                 font=("Microsoft YaHei UI", 9), fg=self.fg2, bg=self.bg,
                 justify="left").pack(pady=(12, 16))
        self.btn_primary("开始安装", self.show_license)

    def show_license(self):
        self.clear()
        self.step = 1
        self.heading("软件许可协议")
        self.subtext("请仔细阅读以下协议。勾选「我接受协议」后方可继续安装。")

        license_text = (
            "WordMaster 软件使用协议\n\n"
            "本软件为个人独立开发的学习项目。\n\n"
            "授权：个人用户可免费安装使用，数据存储在本地。\n\n"
            "未经开发者授权，禁止以下行为：\n"
            "  1. 商业盗版和销售\n"
            "  2. 非法传播\n"
            "  3. 修改后重新发布\n\n"
            "开发者：JasonChen\n"
        )

        outer = tk.Frame(self.root, bg="#f0f0f0", relief="solid", borderwidth=1, bd=1)
        outer.pack(fill="x", padx=40, pady=6)

        text_widget = tk.Text(outer, wrap="word", font=("Microsoft YaHei UI", 9),
                              bg="#fafafa", fg="#333", relief="flat", height=10,
                              padx=14, pady=10, state="normal")
        text_widget.insert("1.0", license_text)
        text_widget.configure(state="disabled")
        text_widget.pack(fill="x")

        # Checkbox with visible feedback
        self.license_var = tk.BooleanVar(value=False)
        cb_frame = tk.Frame(self.root, bg=self.bg)
        cb_frame.pack(pady=10)
        cb = tk.Checkbutton(cb_frame, text="我接受协议", variable=self.license_var,
                            font=("Microsoft YaHei UI", 11, "bold"),
                            bg=self.bg, fg="#1a1a1c",
                            activebackground=self.bg,
                            selectcolor=self.bg,
                            command=lambda: self._update_license_btn())
        cb.pack(side="left")

        # Hint text when not accepted
        self.license_hint = tk.Label(self.root, text="（请先勾选上方选项）",
                                     font=("Microsoft YaHei UI", 8),
                                     fg="#ef4444", bg=self.bg)
        self.license_hint.pack(pady=(0, 4))

        btn_frame = tk.Frame(self.root, bg=self.bg)
        btn_frame.pack(pady=6)
        self.next_btn = tk.Button(btn_frame, text="下一步", command=self.show_path,
                                  font=("Microsoft YaHei UI", 10, "bold"),
                                  bg="#cccccc", fg="white", state="disabled",
                                  relief="flat", padx=32, pady=8, borderwidth=0)
        self.next_btn.pack(side="left", padx=4)
        tk.Button(btn_frame, text="取消", command=self.root.quit,
                  font=("Microsoft YaHei UI", 9), bg="#e0e0e0", fg=self.fg,
                  relief="flat", padx=24, pady=8, borderwidth=0,
                  cursor="hand2").pack(side="left", padx=4)

    def _update_license_btn(self):
        if self.license_var.get():
            self.next_btn.configure(state="normal", bg=self.accent, cursor="hand2")
            self.license_hint.configure(text="")
        else:
            self.next_btn.configure(state="disabled", bg="#cccccc")
            self.license_hint.configure(text="（请先勾选上方选项）")

    def show_path(self):
        self.clear()
        self.step = 2
        self.heading("选择安装位置")
        self.subtext("请选择 WordMaster 的安装目录。")

        tk.Label(self.root, text="安装目录：", font=("Microsoft YaHei UI", 9),
                 fg=self.fg2, bg=self.bg).pack(pady=(16, 4))
        entry_frame = tk.Frame(self.root, bg=self.bg)
        entry_frame.pack(pady=4)
        tk.Entry(entry_frame, textvariable=self.install_dir, font=("Consolas", 10),
                 width=42, relief="solid", borderwidth=1).pack(side="left", padx=(0, 6))
        tk.Button(entry_frame, text="浏览...", command=self._browse_dir,
                  font=("Microsoft YaHei UI", 9), bg="#e0e0e0", relief="flat",
                  padx=12, pady=2, cursor="hand2").pack(side="left")

        self.divider()

        tk.Checkbutton(self.root, text="创建桌面快捷方式", variable=self.create_desktop,
                       font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.fg2,
                       activebackground=self.bg).pack(pady=(12, 2), anchor="w", padx=80)
        tk.Checkbutton(self.root, text="创建开始菜单快捷方式", variable=self.create_startmenu,
                       font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.fg2,
                       activebackground=self.bg).pack(anchor="w", padx=80)

        tk.Label(self.root, text=f"所需空间：约 50 MB", font=("Microsoft YaHei UI", 8),
                 fg=self.fg2, bg=self.bg).pack(pady=(12, 8))

        btn_frame = tk.Frame(self.root, bg=self.bg)
        btn_frame.pack(pady=8)
        self.btn_primary("开始安装", self.do_install)

    def _browse_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(title="选择安装目录", initialdir=self.install_dir.get())
        if d:
            self.install_dir.set(d)

    def do_install(self):
        self.clear()
        self.step = 3
        self.heading("正在安装...")
        progress = ttk.Progressbar(self.root, mode="indeterminate", length=300)
        progress.pack(pady=16)
        progress.start(10)
        self.root.update()

        target = Path(self.install_dir.get())
        try:
            target.mkdir(parents=True, exist_ok=True)
            data_dir = target / "data"
            uninstall_dir = target

            data_dir.mkdir(parents=True, exist_ok=True)

            # Copy EXE
            if BUNDLE_DIR.exists():
                for f in BUNDLE_DIR.iterdir():
                    if f.is_file():
                        shutil.copy2(str(f), str(target / f.name))
                    elif f.is_dir() and f.name != "resources":
                        shutil.copytree(str(f), str(target / f.name), dirs_exist_ok=True)

            # Uninstaller EXE is pre-bundled in the installer, already copied by shutil above

            # Create shortcuts
            if self.create_desktop.get():
                self._create_shortcut("Desktop", target)
            if self.create_startmenu.get():
                self._create_shortcut("StartMenu", target)

            # Register with Windows
            self._register_uninstall(target)

            progress.stop()
            progress.destroy()
            self.show_complete()
        except Exception as e:
            progress.stop()
            messagebox.showerror("安装失败", f"安装过程中出现错误：\n{e}")
            self.root.quit()

    def _create_shortcut(self, location, target):
        exe = target / "WordMaster.exe"
        if not exe.exists():
            return
        if location == "Desktop":
            lnk_dir = Path(os.environ["USERPROFILE"]) / "Desktop"
        else:
            lnk_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
        lnk_dir.mkdir(parents=True, exist_ok=True)
        lnk = lnk_dir / f"{APP_NAME}.lnk"
        # Point IconLocation to the EXE itself (has icon embedded via PyInstaller).
        # win32com in-process COM reliably writes .lnk into shell special folders
        # (e.g. Start Menu), where PowerShell's out-of-process WScript.Shell fails.
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            sc = shell.CreateShortcut(str(lnk))
            sc.TargetPath = str(exe)
            sc.WorkingDirectory = str(target)
            sc.IconLocation = f"{exe},0"
            sc.Description = "WordMaster - AI英语学习助手"
            sc.Save()
        except Exception:
            pass  # Never fail the install because of a shortcut.

    def _register_uninstall(self, target):
        # Per-user registration under HKCU — no admin required.
        import winreg
        exe = target / "WordMaster.exe"
        uninstall = target / "uninstall.exe"
        try:
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WordMaster",
            )
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "WordMaster")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "JasonChen")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(exe))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstall}"')
            winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninstall}"')
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(target))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 51200)
            winreg.CloseKey(key)
        except Exception:
            pass  # Never fail the install because of a registry write.

    def show_complete(self):
        self.clear()
        self.step = 4
        tk.Label(self.root, text="✅", font=("", 48), bg=self.bg).pack(pady=(30, 8))
        self.heading("安装完成！")
        self.subtext(f"WordMaster 已成功安装到：\n{self.install_dir.get()}")
        self.divider()

        tk.Label(self.root, text="内置词库：CET4 / CET6 / IELTS / TOEFL / 高中英语",
                 font=("Microsoft YaHei UI", 9), fg=self.fg2, bg=self.bg).pack(pady=(8, 2))
        tk.Label(self.root, text="桌面快捷方式已创建，双击启动软件。",
                 font=("Microsoft YaHei UI", 9), fg=self.fg2, bg=self.bg).pack(pady=2)

        if self.create_desktop.get():
            self.btn_primary("立即运行 WordMaster", self._launch_and_exit)
        self.btn_secondary("完成", self.root.quit)

    def _launch_and_exit(self):
        exe = Path(self.install_dir.get()) / "WordMaster.exe"
        if exe.exists():
            os.startfile(str(exe))
        self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # Ensure we're running as admin for proper installation
    installer = Installer()
    installer.run()
