; ---------------------------------------------------------------------------
; SolidWorks Semantic Engine - Inno Setup Script
; Produces: swse-setup-1.0.0.exe
; Build with:  iscc installer.iss
; ---------------------------------------------------------------------------

#define MyAppName      "SolidWorks Semantic Engine"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "SWSE Project"
#define MyAppURL       "https://github.com/SamuraiBuddha/sw-semantic-engine"

[Setup]
AppId={{B2C3D4E5-F6A7-8901-BCDE-F12345678901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\SolidWorks Semantic Engine
DefaultGroupName={#MyAppName}
OutputDir=dist
OutputBaseFilename=swse-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=
LicenseFile=
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Add-in DLL and dependencies from Release build
Source: "addin\bin\Release\SolidWorksSemanticEngine.dll";   DestDir: "{app}\addin"; Flags: ignoreversion
Source: "addin\bin\Release\SolidWorksSemanticEngine.pdb";   DestDir: "{app}\addin"; Flags: ignoreversion
Source: "addin\bin\Release\Newtonsoft.Json.dll";            DestDir: "{app}\addin"; Flags: ignoreversion
Source: "addin\bin\Release\SolidWorksSemanticEngine.addin"; DestDir: "{app}\addin"; Flags: ignoreversion

; SolidWorks interop assemblies (needed at runtime)
Source: "addin\bin\Release\SolidWorks.Interop.sldworks.dll";    DestDir: "{app}\addin"; Flags: ignoreversion
Source: "addin\bin\Release\SolidWorks.Interop.swconst.dll";     DestDir: "{app}\addin"; Flags: ignoreversion
Source: "addin\bin\Release\SolidWorks.Interop.swpublished.dll"; DestDir: "{app}\addin"; Flags: ignoreversion

; Backend source (needed for uvicorn)
Source: "backend\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs

; Parameterization module
Source: "parameterization\*"; DestDir: "{app}\parameterization"; Flags: ignoreversion recursesubdirs createallsubdirs

; Training pipeline
Source: "training_pipeline\*"; DestDir: "{app}\training_pipeline"; Flags: ignoreversion recursesubdirs createallsubdirs

; Root files
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "Modelfile";         DestDir: "{app}"; Flags: ignoreversion

[Run]
; Create Python venv
Filename: "python"; Parameters: "-m venv ""{app}\.venv"""; \
    StatusMsg: "Creating Python virtual environment..."; Flags: runhidden waituntilterminated

; Install pip requirements
Filename: "{app}\.venv\Scripts\pip.exe"; Parameters: "install -r ""{app}\requirements.txt"" --quiet"; \
    StatusMsg: "Installing Python dependencies..."; Flags: runhidden waituntilterminated

; Register COM add-in
Filename: "{dotnet40}\RegAsm.exe"; Parameters: "/codebase ""{app}\addin\SolidWorksSemanticEngine.dll"""; \
    StatusMsg: "Registering COM add-in..."; Flags: runhidden waituntilterminated

; Create Ollama model (best-effort)
Filename: "{code:GetOllamaExe}"; Parameters: "create sw-semantic-7b -f ""{app}\Modelfile"""; \
    StatusMsg: "Creating Ollama model (may take a while)..."; \
    Flags: runhidden waituntilterminated skipifdoesntexist

[UninstallRun]
; Unregister COM add-in
Filename: "{dotnet40}\RegAsm.exe"; Parameters: "/u ""{app}\addin\SolidWorksSemanticEngine.dll"""; \
    Flags: runhidden waituntilterminated

[UninstallDelete]
; Clean up generated files
Type: filesandordirs; Name: "{app}\.venv"
Type: files;          Name: "{app}\addin\swse-config.json"

[Code]
// ------------------------------------------------------------------
// Pascal Script: prerequisite checks and post-install config generation
// ------------------------------------------------------------------

var
  OllamaExePath: string;

function GetOllamaExe(Param: string): string;
begin
  Result := OllamaExePath;
end;

function FindOllama: Boolean;
var
  LocalAppData: string;
  Candidate: string;
begin
  Result := False;

  // Check common install location
  LocalAppData := ExpandConstant('{localappdata}');
  Candidate := LocalAppData + '\Programs\Ollama\ollama.exe';
  if FileExists(Candidate) then
  begin
    OllamaExePath := Candidate;
    Result := True;
    Exit;
  end;

  // Check PATH via registry (simple heuristic)
  Candidate := ExpandConstant('{userappdata}') + '\.ollama\ollama.exe';
  if FileExists(Candidate) then
  begin
    OllamaExePath := Candidate;
    Result := True;
    Exit;
  end;
end;

function CheckPythonVersion: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := Result and (ResultCode = 0);
end;

function InitializeSetup: Boolean;
begin
  Result := True;

  // Check Python
  if not CheckPythonVersion then
  begin
    MsgBox('Python 3.10 or later is required but was not found in PATH.' + #13#10 +
           'Please install Python from https://python.org and try again.',
           mbError, MB_OK);
    Result := False;
    Exit;
  end;

  // Check Ollama
  if not FindOllama then
  begin
    if MsgBox('Ollama was not found on this system.' + #13#10 +
              'The model server will not be available until Ollama is installed.' + #13#10#13#10 +
              'Continue installation anyway?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;
  end;
end;

procedure GenerateConfig;
var
  ConfigPath: string;
  Lines: TArrayOfString;
  AppDir: string;
  OllamaEsc: string;
  AppDirEsc: string;
begin
  AppDir := ExpandConstant('{app}');
  ConfigPath := AppDir + '\addin\swse-config.json';

  // Escape backslashes for JSON
  AppDirEsc := AppDir;
  StringChangeEx(AppDirEsc, '\', '\\', True);

  OllamaEsc := OllamaExePath;
  StringChangeEx(OllamaEsc, '\', '\\', True);

  SetArrayLength(Lines, 12);
  Lines[0]  := '{';
  Lines[1]  := '  "projectRoot": "' + AppDirEsc + '",';
  Lines[2]  := '  "pythonVenvPath": ".venv",';
  Lines[3]  := '  "ollamaExePath": "' + OllamaEsc + '",';
  Lines[4]  := '  "backendPort": 8000,';
  Lines[5]  := '  "ollamaPort": 11434,';
  Lines[6]  := '  "autoLaunchBackend": true,';
  Lines[7]  := '  "autoLaunchOllama": true,';
  Lines[8]  := '  "killOnDisconnect": true,';
  Lines[9]  := '  "startupTimeoutMs": 15000';
  Lines[10] := '}';
  Lines[11] := '';

  SaveStringsToFile(ConfigPath, Lines, False);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    GenerateConfig;
  end;
end;
