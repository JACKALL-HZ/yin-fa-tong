# Find Docker WSL vhdx files
Write-Host "=== Look for ext4.vhdx in all of APPDATA ==="
Get-ChildItem -Path "$env:USERPROFILE\AppData" -Recurse -Filter "ext4.vhdx" -ErrorAction SilentlyContinue -Depth 5 | ForEach-Object {
    $sizeGB = [math]::Round($_.Length/1GB, 2)
    Write-Host "$($_.FullName)  ${sizeGB}GB"
}

Write-Host "`n=== Look for any .vhdx files ==="
Get-ChildItem -Path "$env:USERPROFILE\AppData\Local\Docker" -Recurse -Filter "*.vhdx" -ErrorAction SilentlyContinue -Depth 6 | ForEach-Object {
    $sizeGB = [math]::Round($_.Length/1GB, 2)
    Write-Host "$($_.FullName)  ${sizeGB}GB"
}

Write-Host "`n=== Docker WSL directory tree ==="
Get-ChildItem -Path "$env:LOCALAPPDATA\Docker\wsl" -Recurse -Depth 3 -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.PSIsContainer) {
        Write-Host "[DIR] $($_.FullName)"
    } else {
        $sizeMB = [math]::Round($_.Length/1MB, 1)
        Write-Host "      $($_.Name)  ${sizeMB}MB"
    }
}

Write-Host "`n=== Check WSL distros with data distro ==="
wsl --list --all
