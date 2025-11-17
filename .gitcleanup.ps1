# Script để xóa các file không cần thiết khỏi Git tracking
# Sử dụng: .\.gitcleanup.ps1

Write-Host "🧹 Đang xóa các file không cần thiết khỏi Git tracking..." -ForegroundColor Cyan

# Xóa node_modules trong backend (nếu có)
if (Test-Path "backend/node_modules") {
    Write-Host "  - Xóa backend/node_modules/" -ForegroundColor Yellow
    git rm -r --cached backend/node_modules/ 2>&1 | Out-Null
}

# Xóa package files trong backend
if (git ls-files backend/package.json 2>&1) {
    Write-Host "  - Xóa backend/package.json và package-lock.json" -ForegroundColor Yellow
    git rm --cached backend/package.json backend/package-lock.json 2>&1 | Out-Null
}

# Xóa frontend folder trong backend
if (Test-Path "backend/frontend") {
    Write-Host "  - Xóa backend/frontend/" -ForegroundColor Yellow
    git rm -r --cached backend/frontend/ 2>&1 | Out-Null
}

# Xóa file_index files
$fileIndexes = git ls-files | Select-String -Pattern "file_index_.*\.json"
if ($fileIndexes) {
    Write-Host "  - Xóa file_index_*.json files" -ForegroundColor Yellow
    git ls-files | Select-String -Pattern "file_index_.*\.json" | ForEach-Object {
        git rm --cached $_.Line 2>&1 | Out-Null
    }
}

# Xóa database files (nếu có)
$dbFiles = git ls-files | Select-String -Pattern "\.(db|sqlite3)$"
if ($dbFiles) {
    Write-Host "  - Xóa database files" -ForegroundColor Yellow
    $dbFiles | ForEach-Object {
        git rm --cached $_.Line 2>&1 | Out-Null
    }
}

# Xóa log files (nếu có)
$logFiles = git ls-files | Select-String -Pattern "logs/.*\.(log|jsonl)$"
if ($logFiles) {
    Write-Host "  - Xóa log files" -ForegroundColor Yellow
    $logFiles | ForEach-Object {
        git rm --cached $_.Line 2>&1 | Out-Null
    }
}

Write-Host "✅ Hoàn tất! Các file đã được xóa khỏi Git tracking." -ForegroundColor Green
Write-Host ""
Write-Host "📝 Bước tiếp theo:" -ForegroundColor Cyan
Write-Host "   1. Kiểm tra: git status" -ForegroundColor White
Write-Host "   2. Commit: git commit -m 'chore: remove unnecessary files from git tracking'" -ForegroundColor White
Write-Host "   3. Push: git push origin <branch-name>" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Lưu ý: Các file này vẫn còn trong Git history. Để xóa hoàn toàn khỏi history," -ForegroundColor Yellow
Write-Host "   bạn cần sử dụng git filter-branch hoặc BFG Repo-Cleaner (cẩn thận với force push!)" -ForegroundColor Yellow

