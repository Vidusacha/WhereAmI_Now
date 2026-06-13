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

Write-Host "Registry entries created successfully!"
