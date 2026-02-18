[Setup]
AppName=DrivingExamsAnalyzer
AppVersion=1.0
AppPublisher=PoppiApps
DefaultDirName={autopf}\DrivingExamsAnalyzer
DefaultGroupName=DrivingExamsAnalyzer
OutputDir=installer_output
OutputBaseFilename=DrivingExamsAnalyzerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\DrivingExamsAnalyzer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\DrivingExamsAnalyzer"; Filename: "{app}\DrivingExamsAnalyzer.exe"
Name: "{commondesktop}\DrivingExamsAnalyzer"; Filename: "{app}\DrivingExamsAnalyzer.exe"

[Run]
Filename: "{app}\DrivingExamsAnalyzer.exe"; Description: "Launch Driving Exams Analyzer"; Flags: nowait postinstall skipifsilent
