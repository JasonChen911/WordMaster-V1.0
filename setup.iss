; WordMaster Installer Script — Inno Setup 6
; Bilingual (Chinese Simplified / English) with license agreement

#define AppName "WordMaster"
#define AppVersion "0.1.0"
#define AppPublisher "JasonChen"
#define AppContact "cby080812b@outlook.com"

[Setup]
AppId={{B8F4A3D2-7E61-4C92-A1F5-D9E3C6B8021A}}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} v{#AppVersion} Beta
AppPublisher={#AppPublisher}
AppPublisherURL=mailto:{#AppContact}
AppSupportURL=mailto:{#AppContact}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=license_agreement.txt
OutputDir=installer_output
OutputBaseFilename=WordMaster_Setup
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
ShowLanguageDialog=yes

[Messages]
; English fallback messages
SetupAppTitle={#AppName} Setup
SetupWindowTitle={#AppName} v{#AppVersion} Beta — Setup
BeveledLabel={#AppName} v{#AppVersion} Beta · {#AppPublisher}

[CustomMessages]
; Bilingual strings used in the script
en.AppNameAndVer={#AppName} v{#AppVersion} Beta
en.SelectDirDesc=Setup will install {#AppName} to the following folder.
en.SelectDirBrowse=To continue, click Next. To choose a different folder, click Browse.
en.DesktopIconDesc=Create &desktop shortcut
en.LaunchAfterInstall=Launch {#AppName}
en.LicenseTitle={#AppName} Software License Agreement
en.LicenseText=This software is currently in internal Beta testing phase.%n%nUnauthorized copying, redistribution, modification, repackaging,%nor commercial use of this software is strictly prohibited%nwithout the author's permission.%n%nDeveloper: {#AppPublisher}%nContact: {#AppContact}%n%n{#AppName} is a personal English vocabulary learning tool.%nThank you for using {#AppName}.

cn.AppNameAndVer={#AppName} v{#AppVersion} Beta
cn.SelectDirDesc=安装程序将把 {#AppName} 安装到以下文件夹。
cn.SelectDirBrowse=点击"下一步"继续。如需选择其他文件夹，请点击"浏览"。
cn.DesktopIconDesc=创建桌面快捷方式(&D)
cn.LaunchAfterInstall=立即运行 {#AppName}
cn.LicenseTitle={#AppName} 软件使用协议
cn.LicenseText=本软件目前处于内部 Beta 测试阶段。%n%n未经作者允许，禁止对本软件进行盗版传播、修改、%n二次打包或商业用途。%n%n软件制作人：{#AppPublisher}%n联系邮箱：{#AppContact}%n%n{#AppName} 是一款用于英语词汇学习的个人学习工具。%n感谢使用 {#AppName}。

[Languages]
Name: "cn"; MessagesFile: "ChineseSimplified.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIconDesc}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\WordMaster.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "resources\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\WordMaster.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\WordMaster.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{autoprograms}\卸载 {#AppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\icon.ico"

[Run]
Filename: "{app}\WordMaster.exe"; Description: "{cm:LaunchAfterInstall}"; Flags: nowait postinstall skipifsilent
