# PowerShell script to build Flutter Web and update web_dist

Write-Host "1. Building Flutter Web project..." -ForegroundColor Cyan
Set-Location -Path frontend
flutter build web --release

if ($LASTEXITCODE -ne 0) {
    Write-Error "Flutter build failed!"
    exit $LASTEXITCODE
}

Write-Host "2. Updating web_dist folder..." -ForegroundColor Cyan
# Clean existing files in web_dist
if (Test-Path -Path web_dist) {
    Remove-Item -Path web_dist\* -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -Path web_dist -ItemType Directory -Force
}

# Copy newly built files to web_dist
Copy-Item -Path build\web\* -Destination web_dist -Recurse -Force

Write-Host "3. Building Docker image for frontend..." -ForegroundColor Cyan
Set-Location -Path ..
docker-compose build frontend

Write-Host "4. Restarting frontend container..." -ForegroundColor Cyan
docker-compose up -d frontend

Write-Host "Frontend build and deploy completed successfully!" -ForegroundColor Green
