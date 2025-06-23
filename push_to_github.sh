#!/bin/bash

# Navigate to the project directory
cd "/Users/aayushkher/Desktop/project plumber"

# Check git status
echo "Checking git status..."
git status

# Check if remote is already configured
echo "Checking remote configuration..."
git remote -v

# Add the remote if it doesn't exist
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "Adding remote origin..."
    git remote add origin https://github.com/Aayushhkher/plumbing.git
fi

# Add all files
echo "Adding all files..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Initial commit - Plumber matching application"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done!" 