"""WordMaster Uninstaller — standalone Windows GUI."""

import os, sys, shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "WordMaster"
# PyInstaller --onefile extracts to temp dir; sys.executable gives the real EXE location
INSTALL_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent


class Uninstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"卸载 {APP_NAME}")
        self.root.geometry("500x420")
        self.root.minsize(460, 380)
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

        self.accent = "#6366f1"
        self.fg = "#1a1a1c"
        self.fg2 = "#6b6b70"
        self.bg = "#f5f5f5"

        self.create_desktop = tk.BooleanVar(value=True)
        self.create_startmenu = tk.BooleanVar(value=True)
        self.remove_data = tk.BooleanVar(value=False)

        self.show_confirm()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def show_confirm(self):
        self.clear()
        tk.Label(self.root, text="🗑", font=("", 48), bg=self.bg).pack(pady=(24, 8))
        tk.Label(self.root, text="卸载 WordMaster", font=("Microsoft YaHei UI", 16, "bold"),
                 fg=self.fg, bg=self.bg).pack(pady=4)
        tk.Label(self.root, text="请确认要删除的内容：", font=("Microsoft YaHei UI", 9),
                 fg=self.fg2, bg=self.bg).pack(pady=(4, 16))

        # Options
        opts = tk.Frame(self.root, bg=self.bg)
        opts.pack(pady=4)
        tk.Checkbutton(opts, text="删除程序文件 (WordMaster.exe, resources/)",
                       variable=tk.BooleanVar(value=True),
                       font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.fg,
                       state="disabled").pack(anchor="w", pady=2)

        tk.Checkbutton(opts, text="删除桌面快捷方式", variable=self.create_desktop,
                       font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.fg,
                       activebackground=self.bg).pack(anchor="w", pady=2)

        tk.Checkbutton(opts, text="删除开始菜单快捷方式", variable=self.create_startmenu,
                       font=("Microsoft YaHei UI", 9), bg=self.bg, fg=self.fg,
                       activebackground=self.bg).pack(anchor="w", pady=2)

        tk.Checkbutton(opts, text="同时删除学习数据 (数据库 + 音频缓存)",
                       variable=self.remove_data,
                       font=("Microsoft YaHei UI", 9, "bold"), bg=self.bg,
                       fg="#ef4444", activebackground=self.bg).pack(anchor="w", pady=(8, 2))

        tk.Label(self.root, text="⚠ 删除学习数据不可恢复！", font=("Microsoft YaHei UI", 8),
                 fg="#ef4444", bg=self.bg).pack(pady=(0, 2))

        # Separator
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=30, pady=(8, 0))

        # Bottom action bar — always visible at the bottom
        btn_frame = tk.Frame(self.root, bg=self.bg)
        btn_frame.pack(side="bottom", fill="x", padx=30, pady=(6, 14))
        tk.Button(btn_frame, text="确认卸载", command=self.do_uninstall,
                  font=("Microsoft YaHei UI", 10, "bold"), bg="#ef4444", fg="white",
                  activebackground="#dc2626", relief="flat", padx=32, pady=10,
                  borderwidth=0, cursor="hand2").pack(side="right", padx=4)
        tk.Button(btn_frame, text="取消", command=self.root.quit,
                  font=("Microsoft YaHei UI", 10), bg="#e0e0e0", fg=self.fg,
                  relief="flat", padx=32, pady=10, borderwidth=0,
                  cursor="hand2").pack(side="right", padx=4)

    def do_uninstall(self):
        self.clear()
        tk.Label(self.root, text="⏳", font=("", 40), bg=self.bg).pack(pady=(30, 8))
        tk.Label(self.root, text="正在卸载...", font=("Microsoft YaHei UI", 14, "bold"),
                 fg=self.fg, bg=self.bg).pack(pady=4)
        self.root.update()

        try:
            import subprocess

            # 1. Remove shortcuts
            desktop = Path(os.environ["USERPROFILE"]) / "Desktop" / f"{APP_NAME}.lnk"
            if desktop.exists():
                desktop.unlink()
            start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / APP_NAME
            if start_menu.exists():
                shutil.rmtree(str(start_menu), ignore_errors=True)

            # 2. Kill main app if running
            subprocess.run(['taskkill', '/f', '/im', 'WordMaster.exe'],
                           capture_output=True)

            # 3. Remove registry entry (HKCU — per-user install, no admin)
            try:
                import winreg
                winreg.DeleteKey(
                    winreg.HKEY_CURRENT_USER,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WordMaster",
                )
            except OSError:
                pass  # Already removed or never registered

            # 4. Write cleanup VBScript to %TEMP% and launch it DETACHED.
            #    VBScript runs completely silently - no CMD window, no console.
            #    It waits for uninstaller.exe to exit, then deletes everything.
            install_dir = str(INSTALL_DIR)
            DETACHED = 0x00000008
            CREATE_NO_WINDOW = 0x08000000

            if self.remove_data.get():
                data_dir = Path(os.environ["APPDATA"]) / "WordMaster"
                data_line = f'DeleteFolder "{data_dir}"'
            else:
                data_line = 'rem user data preserved'

            vbs_path = os.environ["TEMP"] + "\\wm_cleanup.vbs"
            with open(vbs_path, 'w') as f:
                f.write(f'''Dim fso, dir, count
Set fso = CreateObject("Scripting.FileSystemObject")
dir = "{install_dir}"
count = 0
Do While fso.FileExists(dir & "\\uninstall.exe") And count < 30
    WScript.Sleep 1000
    count = count + 1
Loop
WScript.Sleep 1500
On Error Resume Next
fso.DeleteFolder dir, True
{data_line}
fso.DeleteFile WScript.ScriptFullName
''')

            # Launch detached: the VBS process survives after we exit, no window ever
            subprocess.Popen(
                ['wscript.exe', '//B', vbs_path],
                creationflags=DETACHED | CREATE_NO_WINDOW,
                close_fds=True)

            # Also try immediate deletion of files that aren't locked
            for item in INSTALL_DIR.iterdir():
                if item.name in ('uninstall.exe', 'data'):
                    continue
                try:
                    if item.is_dir():
                        shutil.rmtree(str(item), ignore_errors=True)
                    else:
                        item.unlink()
                except Exception:
                    pass

            self.show_done()
        except Exception as e:
            messagebox.showerror("卸载失败", f"卸载出错：{e}")
            self.root.quit()

    def show_done(self):
        self.clear()
        tk.Label(self.root, text="✅", font=("", 48), bg=self.bg).pack(pady=(30, 8))
        tk.Label(self.root, text="卸载完成", font=("Microsoft YaHei UI", 16, "bold"),
                 fg=self.fg, bg=self.bg).pack(pady=4)
        if self.remove_data.get():
            tk.Label(self.root, text="程序文件、快捷方式和学习数据均已删除。",
                     font=("Microsoft YaHei UI", 9), fg=self.fg2, bg=self.bg).pack(pady=4)
        else:
            tk.Label(self.root, text="程序文件已删除，学习数据已保留。",
                     font=("Microsoft YaHei UI", 9), fg=self.fg2, bg=self.bg).pack(pady=4)
            data_path = Path(os.environ["APPDATA"]) / "WordMaster"
            tk.Label(self.root, text=f"数据位置：{data_path}",
                     font=("Microsoft YaHei UI", 8), fg=self.fg2, bg=self.bg).pack()
        tk.Button(self.root, text="完成", command=self.root.quit,
                  font=("Microsoft YaHei UI", 10, "bold"), bg=self.accent, fg="white",
                  relief="flat", padx=32, pady=8, borderwidth=0,
                  cursor="hand2").pack(pady=16)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Uninstaller().run()
