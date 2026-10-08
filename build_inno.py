import os
import sys
import subprocess

def create_nsis_or_inno():
    # Write Inno Setup Script
    inno_script = r"""[Setup]
AppName=Juridico.Code
AppVersion=1.0.0
DefaultDirName={autopf}\JuridicoCode
DefaultGroupName=Juridico.Code
OutputDir=dist
OutputBaseFilename=Setup_Juridico_Code
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion; Excludes: ".git,build,dist,__pycache__,*.pyc"

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;
"""
    with open("setup_script.iss", "w", encoding="utf-8") as f:
        f.write(inno_script)
    print("[*] Script Inno Setup criado: setup_script.iss")

if __name__ == "__main__":
    create_nsis_or_inno()
