#!/bin/bash

# Build script for AWS Amplify
# This script handles the build process in a more robust way

set -e  # Exit on any error

echo "=== AI Dialer Amplify Build Script ==="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "=== Checking for amplify_ui directory ==="
if [ ! -d "amplify_ui" ]; then
    echo "❌ ERROR: amplify_ui directory not found!"
    echo "Available directories:"
    ls -la
    exit 1
fi

echo "✅ amplify_ui directory found"
echo "Contents of amplify_ui:"
ls -la amplify_ui/

echo "=== Installing dependencies ==="
cd amplify_ui
npm ci

echo "=== Building React application ==="
npm run build

echo "=== Build completed successfully ==="
echo "Build output:"
ls -la build/

echo "✅ Build script completed successfully" 