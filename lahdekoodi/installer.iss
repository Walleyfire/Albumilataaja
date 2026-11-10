#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#ifndef PackageDir
  #define PackageDir ".."
#endif
#ifndef OutputDirPath
  #define OutputDirPath "..\.."
#endif
[Setup]
AppId={{D2414ED4-C8AA-4D8B-9F85-B8074C7894DE}
AppName=Albumilataaja
AppVersion={#AppVersion}
AppPublisher=Walleyfire
AppPublisherURL=https://github.com/Walleyfire/Albumilataaja
AppSupportURL=https://github.com/Walleyfire/Albumilataaja/issues
AppUpdatesURL=https://github.com/Walleyfire/Albumilataaja/releases
DefaultDirName={localappdata}\Programs\Albumilataaja
DefaultGroupName=Albumilataaja
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDirPath}
OutputBaseFilename=Albumilataaja-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
CloseApplicationsFilter=Albumilataaja.exe
RestartApplications=no
UninstallDisplayIcon={app}\Albumilataaja.exe
SetupLogging=yes
[Languages]
Name: "finnish"; MessagesFile: "compiler:Languages\Finnish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Luo pikakuvake työpöydälle"; GroupDescription: "Pikakuvakkeet:"
[Files]
Source: "{#PackageDir}\Albumilataaja.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PackageDir}\tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PackageDir}\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PackageDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PackageDir}\THIRD_PARTY.md"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Albumilataaja"; Filename: "{app}\Albumilataaja.exe"
Name: "{autodesktop}\Albumilataaja"; Filename: "{app}\Albumilataaja.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\Albumilataaja.exe"; Description: "Käynnistä Albumilataaja"; Flags: nowait postinstall skipifsilent
