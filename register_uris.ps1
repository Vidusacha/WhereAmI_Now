# Register DBeaver handler
New-Item -Path "HKCU:\Software\Classes\whereami-dbeaver" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-dbeaver" -Name "(default)" -Value "URL:WhereAmI DBeaver Protocol" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-dbeaver" -Name "URL Protocol" -Value "" -Force | Out-Null
New-Item -Path "HKCU:\Software\Classes\whereami-dbeaver\shell\open\command" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-dbeaver\shell\open\command" -Name "(default)" -Value '"C:\Program Files\DBeaver\dbeaver.exe" -con "driver=postgresql|host=localhost|port=5432|database=whereami_db|user=admin|password=securepassword123"' -Force | Out-Null

# Register SSH handler
New-Item -Path "HKCU:\Software\Classes\whereami-ssh" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-ssh" -Name "(default)" -Value "URL:WhereAmI SSH Protocol" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-ssh" -Name "URL Protocol" -Value "" -Force | Out-Null
New-Item -Path "HKCU:\Software\Classes\whereami-ssh\shell\open\command" -Force | Out-Null

# We use powershell to parse the URL and launch docker exec
$sshCmd = 'powershell.exe -NoProfile -Command "$c = ''%1'' -replace ''^whereami-ssh://|/$'', ''''; docker exec -it $c /bin/sh"'
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-ssh\shell\open\command" -Name "(default)" -Value $sshCmd -Force | Out-Null

# Register Folder Handler
New-Item -Path "HKCU:\Software\Classes\whereami-folder" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-folder" -Name "(default)" -Value "URL:WhereAmI Folder Protocol" -Force | Out-Null
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-folder" -Name "URL Protocol" -Value "" -Force | Out-Null
New-Item -Path "HKCU:\Software\Classes\whereami-folder\shell\open\command" -Force | Out-Null

# Parse URL, URL decode the entity name, and open explorer
$folderCmd = 'powershell.exe -NoProfile -WindowStyle Hidden -Command "$url = ''%1''; $entity = $url -replace ''^whereami-folder://|/$'', ''''; if ($entity) { Add-Type -AssemblyName System.Web; $entity = [System.Web.HttpUtility]::UrlDecode($entity); $path = Join-Path ''D:\Workarea\Project WhereAmI_Now\data\scraped_documents'' $entity; if (-not (Test-Path $path)) { New-Item -ItemType Directory -Force -Path $path | Out-Null }; Start-Process explorer.exe -ArgumentList \"`\"$path`\"\" } else { Start-Process explorer.exe -ArgumentList ''"D:\Workarea\Project WhereAmI_Now\data\scraped_documents"'' }"'
New-ItemProperty -Path "HKCU:\Software\Classes\whereami-folder\shell\open\command" -Name "(default)" -Value $folderCmd -Force | Out-Null

Write-Host "Registry entries created successfully!"
