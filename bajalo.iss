[Setup]
AppName=Bájalo
AppVersion=1.0
AppPublisher=Jair
DefaultDirName={autopf}\Bajalo
DefaultGroupName=Bájalo
OutputDir=instalador
OutputBaseFilename=Instalador-Bajalo
SetupIconFile=bajalo.ico
UninstallDisplayIcon={app}\Bajalo.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\Bajalo\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Bájalo"; Filename: "{app}\Bajalo.exe"
Name: "{autodesktop}\Bájalo"; Filename: "{app}\Bajalo.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Bajalo.exe"; Description: "Abrir Bájalo"; Flags: nowait postinstall skipifsilent
