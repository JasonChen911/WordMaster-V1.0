; Chinese Simplified language file for WordMaster Installer
; Based on Inno Setup Default.isl format

[LangOptions]
LanguageName=简体中文
LanguageID=$0804
LanguageCodePage=936
DialogFontName=Microsoft YaHei
DialogFontSize=9
WelcomeFontName=Microsoft YaHei
WelcomeFontSize=14

[Messages]

; Application titles
SetupAppTitle=安装程序
SetupWindowTitle=安装 - %1
UninstallAppTitle=卸载程序
UninstallAppFullTitle=%1 卸载

; Misc. common
InformationTitle=信息
ConfirmTitle=确认
ErrorTitle=错误

; SetupLdr messages
SetupLdrStartupMessage=即将安装 %1。是否继续？
LdrCannotCreateTemp=无法创建临时文件。安装中止。
LdrCannotExecTemp=无法在临时目录中执行文件。安装中止。

; Startup error messages
LastErrorMessage=%1。%n%n错误 %2: %3
SetupFileMissing=安装目录中缺少文件 %1。请修复此问题或获取一个新版本的程序。
SetupFileCorrupt=安装文件已损坏。请获取一个新版本的程序。
SetupFileCorruptOrWrongVer=安装文件已损坏，或与此版本的安装程序不兼容。
InvalidParameter=传入了无效的命令行参数:%n%n%1
SetupAlreadyRunning=安装程序已在运行。
WindowsVersionNotSupported=此程序不支持您计算机上运行的 Windows 版本。
WindowsServicePackRequired=此程序需要 %1 Service Pack %2 或更高版本。
NotOnThisPlatform=此程序无法在 %1 上运行。
OnlyOnThisPlatform=此程序必须在 %1 上运行。
OnlyOnTheseArchitectures=此程序只能安装在为以下处理器架构设计的 Windows 版本上:%n%n%1
WinVersionTooLowError=此程序需要 %1 版本 %2 或更高版本。
WinVersionTooHighError=此程序无法安装在 %1 版本 %2 或更高版本上。
AdminPrivilegesRequired=安装此程序时必须以管理员身份登录。
PowerUserPrivilegesRequired=安装此程序时必须以管理员或 Power Users 组成员的身份登录。
SetupAppRunningError=安装程序检测到 %1 当前正在运行。%n%n请立即关闭它的所有实例，然后点击"确定"继续，或点击"取消"退出。
UninstallAppRunningError=卸载程序检测到 %1 当前正在运行。%n%n请立即关闭它的所有实例，然后点击"确定"继续，或点击"取消"退出。

; Setup questions
PrivilegesRequiredOverrideTitle=选择安装模式
PrivilegesRequiredOverrideInstruction=选择安装模式
PrivilegesRequiredOverrideText1=%1 可以为所有用户安装（需要管理员权限），或仅为您自己安装。
PrivilegesRequiredOverrideText2=%1 可以仅为您自己安装，或为所有用户安装（需要管理员权限）。
PrivilegesRequiredOverrideAllUsers=为所有用户安装(&A)
PrivilegesRequiredOverrideAllUsersRecommended=为所有用户安装（推荐）(&A)
PrivilegesRequiredOverrideCurrentUser=仅为我安装(&M)
PrivilegesRequiredOverrideCurrentUserRecommended=仅为我安装（推荐）(&M)

; Misc. errors
ErrorCreatingDir=安装程序无法创建目录 "%1"
ErrorTooManyFilesInDir=无法在目录 "%1" 中创建文件，因为它包含太多文件

; Setup common messages
ExitSetupTitle=退出安装程序
ExitSetupMessage=安装未完成。如果现在退出，程序将不会被安装。%n%n您可以稍后再次运行安装程序来完成安装。%n%n是否退出安装？
AboutSetupMenuItem=关于安装程序(&A)...
AboutSetupTitle=关于安装程序
AboutSetupMessage=%1 version %2%n%nCopyright (C) 1997-2026 Jordan Russell.%n%nPortions Copyright (C) 2000-2026 Martijn Laan.
AboutSetupNote=
TranslatorNote=

; Buttons
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonOK=确定
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonYesToAll=全部是(&A)
ButtonNo=否(&N)
ButtonNoToAll=全部否(&O)
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
ButtonWizardBrowse=浏览(&B)...
ButtonNewFolder=新建文件夹(&M)

; "Select Language" dialog
SelectLanguageTitle=选择安装语言
SelectLanguageLabel=请选择安装语言：

; Common wizard text
ClickNext=点击"下一步"继续，或点击"取消"退出安装程序。
BeveledLabel=
BrowseDialogTitle=浏览文件夹
BrowseDialogLabel=请选择一个文件夹，然后点击"确定"。
NewFolderName=新建文件夹

; "Welcome" wizard page
WelcomeLabel1=欢迎安装 [name]
WelcomeLabel2=即将在您的电脑上安装 [name/ver]。%n%n建议在继续之前关闭所有其他应用程序。

; "Password" wizard page
WizardPassword=密码
PasswordLabel1=此安装受密码保护。
PasswordLabel2=请输入密码，然后点击"下一步"继续。密码区分大小写。
PasswordEditLabel=密码(&P):
IncorrectPassword=密码不正确，请重新输入。

; "License Agreement" wizard page
WizardLicense=许可协议
LicenseLabel=请在继续之前阅读以下重要信息。
LicenseLabel3=请阅读以下许可协议。您必须接受协议才能继续安装。
LicenseAccepted=我接受协议(&A)
LicenseNotAccepted=我不同意(&D)

; "Information" wizard pages
WizardInfoBefore=信息
InfoBeforeLabel=请在继续之前阅读以下重要信息。
InfoBeforeClickLabel=当您准备好继续时，请点击"下一步"。
WizardInfoAfter=信息
InfoAfterLabel=请阅读以下重要信息。
InfoAfterClickLabel=当您准备好继续时，请点击"下一步"。

; "User Information" wizard page
WizardUserInfo=用户信息
UserInfoLabel=请输入您的信息。
UserInfoName=用户名(&U):
UserInfoOrg=组织(&O):
UserInfoSerial=序列号(&S):
UserInfoNameRequired=您必须输入用户名。

; "Select Destination Location" wizard page
WizardSelectDir=选择安装位置
SelectDirLabel3=安装程序将把 [name] 安装到以下文件夹。
SelectDirBrowseLabel=点击"下一步"继续。如需选择其他文件夹，请点击"浏览"。
DiskSpaceMBLabel=至少需要 [mb] MB 的可用磁盘空间。
CannotCreateDir=安装程序无法创建目录 "%1"。
ToUNCPathname=无法将网络路径作为安装目录。请选择本地文件夹。
InvalidPath=您必须输入包含驱动器号的完整路径，例如:%n%nC:\APP%n%n或者 UNC 路径，格式为:%n%n\\server\share
InvalidDrive=您选择的驱动器或 UNC 共享不存在或无法访问。请选择其他位置。
DiskSpaceWarningTitle=磁盘空间不足
DiskSpaceWarning=安装程序至少需要 %1 KB 的可用空间，但所选驱动器只有 %2 KB 的可用空间。%n%n是否继续？
DirNameTooLong=文件夹名或路径太长。
InvalidDirName=文件夹名无效。
BadDirName32=文件夹名不能包含以下任何字符:%n%n%1
DirExistsTitle=文件夹已存在
DirExists=文件夹:%n%n%1%n%n已存在。是否仍要安装到此文件夹？
DirDoesntExistTitle=文件夹不存在
DirDoesntExist=文件夹:%n%n%1%n%n不存在。是否要创建它？
DiskSpaceUnit=KB，字节

; "Select Components" wizard page
WizardSelectComponents=选择组件
SelectComponentsLabel=选择您要安装的组件；清除您不想安装的组件。点击"下一步"继续。
SelectComponentsDesc=将鼠标悬停在组件上可查看其说明。
FullInstallation=完整安装
CompactInstallation=紧凑安装
CustomInstallation=自定义安装
NoIconsCheck=不创建任何图标
ComponentsDiskSpaceMBLabel=当前选择至少需要 [mb] MB 的磁盘空间。

; "Select Start Menu Folder" wizard page
WizardSelectProgramGroup=选择开始菜单文件夹
SelectStartMenuFolderLabel3=安装程序将在以下开始菜单文件夹中创建快捷方式。
SelectStartMenuFolderBrowseLabel=点击"下一步"继续。如需选择其他文件夹，请点击"浏览"。
MustEnterGroupName=您必须输入文件夹名。
GroupNameTooLong=文件夹名或路径太长。
InvalidGroupName=文件夹名无效。
BadGroupName32=文件夹名不能包含以下任何字符:%n%n%1
NoProgramGroupCheck2=不创建开始菜单文件夹(&D)

; "Select Tasks" wizard page
WizardSelectTasks=选择附加任务
SelectTasksLabel2=选择您希望安装程序执行的附加任务，然后点击"下一步"继续。
SelectTasksDesc=将鼠标悬停在任务上可查看其他信息。

; "Ready to Install" wizard page
WizardReady=准备安装
ReadyLabel1=安装程序现在准备好在您的电脑上安装 [name]。
ReadyLabel2a=点击"安装"继续安装，或点击"上一步"查看或更改设置。
ReadyLabel2b=点击"安装"继续安装。
ReadyMemoUserInfo=用户信息:
ReadyMemoDir=安装位置:
ReadyMemoType=安装类型:
ReadyMemoComponents=所选组件:
ReadyMemoGroup=开始菜单文件夹:
ReadyMemoTasks=附加任务:

; "Installing" wizard page
WizardInstalling=正在安装
InstallingLabel=安装程序正在将 [name] 安装到您的电脑上，请稍候。

; "Setup Completed" wizard page
FinishedHeadingLabel=[name] 安装完成
FinishedLabelNoIcons=安装程序已在您的电脑上完成 [name] 的安装。
FinishedLabel=安装程序已在您的电脑上完成 [name] 的安装。可以通过已安装的快捷方式启动应用程序。
ClickFinish=点击"完成"退出安装程序。
FinishedRestartLabel=要完成 [name] 的安装，必须重新启动电脑。是否现在重新启动？
FinishedRestartMessage=要完成 [name] 的安装，必须重新启动电脑。%n%n是否现在重新启动？
ShowReadmeCheck=是否查看自述文件？
YesRestart=是，立即重新启动
NoRestart=不，稍后重新启动

; "Run My Program" check box
RunEntryExec=运行 [name]
RunEntryShellExec=查看 [name] 自述文件

; Uninstaller
UninstallNotFound=找不到卸载程序 "%1"。无法卸载。
UninstallOpenError=无法打开卸载程序 "%1"。无法卸载。
UninstallUnsupportedVer=卸载程序 "%1" 的格式不被此版本的 Windows 识别。无法卸载。
UninstallUnknownEntry=卸载程序遇到一个它无法删除的条目:%n%n%1
ConfirmUninstall=确认卸载
UninstallOnlyOnWin64=此卸载程序只能在 64 位 Windows 上运行。
OnlyAdminUninstall=此程序只能由具有管理员权限的用户卸载。
UninstallStatusLabel=请稍候，正在从您的电脑上删除 [name]。
UninstalledAll=[name] 已成功从您的电脑上删除。
UninstalledMost=[name] 卸载完成。%n%n有些项目未能删除。这些项目可以通过手动方式删除。
UninstalledAndNeedsRestart=要完成 [name] 的卸载，必须重新启动电脑。%n%n是否现在重新启动？
UninstallDataRemoved=不会删除在安装后创建的数据文件。

; Required restart messages
NeedRestart=要完成安装，必须重新启动电脑。是否现在重新启动？

; Tasks
DesktopIconEntry=创建桌面快捷方式(&D)

; Shell message
AppCannotBeClosed=应用程序无法完全关闭。请手动保存工作并关闭所有对话框，然后点击"重试"。

; Post-install error messages
ErrorReadingExistingDest=尝试读取现有文件时发生错误:%n%n%1
