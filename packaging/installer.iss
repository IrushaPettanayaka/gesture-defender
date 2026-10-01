[Setup]
AppId=GestureDefender.Desktop
AppName=Gesture Defender
AppVersion=1.3.0
AppPublisher=Gesture Defender
DefaultDirName={localappdata}\Programs\Gesture Defender
DefaultGroupName=Gesture Defender
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.22000
OutputDir=..\release
OutputBaseFilename=GestureDefender-1.3.0-Setup
SetupIconFile=..\art\game.ico
UninstallDisplayIcon={app}\GestureDefender.exe
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\GestureDefender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gesture Defender"; Filename: "{app}\GestureDefender.exe"
Name: "{autodesktop}\Gesture Defender"; Filename: "{app}\GestureDefender.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GestureDefender.exe"; Description: "Launch Gesture Defender"; Flags: nowait postinstall skipifsilent
