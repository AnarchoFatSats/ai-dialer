# Git Push Script for New Repository Migration
# Run this in PowerShell in the intellereach-new directory

Write-Host "🚀 Starting Git Migration to cerberus100/intellereach" -ForegroundColor Green

# Navigate to the intellereach-new directory
Set-Location "intellereach-new"

# Check git status
Write-Host "📋 Checking git status..." -ForegroundColor Yellow
git status

# Add all files
Write-Host "📦 Adding all files..." -ForegroundColor Yellow
git add .

# Commit changes
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m "Complete migration from AnarchoFatSats/ai-dialer to cerberus100/intellereach with updated deployment configs"

# Set up remote if not already done
Write-Host "🔗 Setting up remote repository..." -ForegroundColor Yellow
git remote add origin https://github.com/cerberus100/intellereach.git

# Push to new repository
Write-Host "⬆️ Pushing to new repository..." -ForegroundColor Yellow
git push -u origin main

Write-Host "✅ Migration complete!" -ForegroundColor Green
Write-Host "🌐 Repository: https://github.com/cerberus100/intellereach" -ForegroundColor Cyan

