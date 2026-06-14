[Setup]
AppId={{3bdc1d26-5674-076c-cb40-5e47ade8e802}
AppName=RixsToolBoxAppVersion=0.8.3
AppVerName=RixsToolBox v0.8.3
AppPublisher=Kurt Kummer
AppPublisherURL=https://github.com/kkummer/RixsToolBox
AppSupportURL=https://github.com/kkummer/RixsToolBox
AppUpdatesURL=https://github.com/kkummer/RixsToolBox/releases
DefaultDirName={pf}\RixsToolBox v0.8.3
DefaultGroupName=RixsToolBox v0.8.3
;LicenseFile=..\LICENSE.txt
OutputDir=.\installer
OutputBaseFilename=RixsToolBox-0.8.3-x64
Compression=lzma
SolidCompression=yes
; Remove for 32-bit applications
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: ".\RixsToolBox v0.8.3\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "icons\logo.ico"; DestDir: "{app}"

[Icons]
; Do not forget to copy logo.ico to the build folder.
Name: "{group}\RixsToolBox"; Filename: "{app}\RixsToolBox.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"