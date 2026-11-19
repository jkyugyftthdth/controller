; Inno Setup script. Build: iscc /DAppVersion=1.0.0 installer\ForzaController.iss  (run from the project root)
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppName "Forza Controller"
#define VigemFile "ViGEmBus_Setup.exe"

[Setup]
AppId={{6D1B7C0E-5A34-4F7B-9C52-2B8E0F4A91D7}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Forza Controller
DefaultDirName={autopf}\ForzaController
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ForzaController-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\ForzaController.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "firewall"; Description: "Allow phone connections through Windows Firewall (TCP port 8443)"; GroupDescription: "Connection:"
#ifexist "ViGEmBus_Setup.exe"
Name: "vigem"; Description: "Install the ViGEmBus gamepad driver (needed for Xbox controller mode)"; GroupDescription: "Controller:"; Check: not ViGEmInstalled
#endif

[Files]
Source: "..\dist\ForzaController.exe"; DestDir: "{app}"; Flags: ignoreversion
#ifexist "ViGEmBus_Setup.exe"
Source: "{#VigemFile}"; DestDir: "{tmp}"; Flags: deleteafterinstall; Tasks: vigem
#endif

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\ForzaController.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\ForzaController.exe"; Tasks: desktopicon

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""Forza Controller"""; Flags: runhidden; Tasks: firewall
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""Forza Controller"" dir=in action=allow protocol=TCP localport=8443 profile=any"; Flags: runhidden; Tasks: firewall
#ifexist "ViGEmBus_Setup.exe"
Filename: "{tmp}\{#VigemFile}"; Parameters: "/passive /promptrestart"; StatusMsg: "Installing the ViGEmBus gamepad driver..."; Tasks: vigem
#endif
Filename: "{app}\ForzaController.exe"; Description: "Start {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""Forza Controller"""; Flags: runhidden; RunOnceId: "DelFirewallRule"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\ForzaController_data"

[Code]
function ViGEmInstalled: Boolean;
begin
  Result := RegKeyExists(HKLM, 'SYSTEM\CurrentControlSet\Services\ViGEmBus');
end;
