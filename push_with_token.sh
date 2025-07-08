#!/bin/bash

# Navigate to the project directory
cd "/Users/aayushkher/Desktop/project plumber"

echo "To push to GitHub, you need to use a Personal Access Token."
echo ""
echo "Here's how to create one:"
echo "1. Go to GitHub.com and sign in"
echo "2. Click your profile picture → Settings"
echo "3. Scroll down and click 'Developer settings' in the sidebar"
echo "4. Click 'Personal access tokens' → 'Tokens (classic)'"
echo "5. Click 'Generate new token' → 'Generate new token (classic)'"
echo "6. Give it a name like 'Plumber Project'"
echo "7. Select scopes: at minimum check 'repo'"
echo "8. Click 'Generate token'"
echo "9. Copy the token (you won't see it again!)"
echo ""
echo "When you run the push command, use your GitHub username and the token as the password."
echo ""

# Change remote URL back to HTTPS
echo "Setting remote URL to HTTPS..."
git remote set-url origin https://github.com/Aayushhkher/plumbing.git

echo "Ready to push! Run the following command:"
echo "git push -u origin main"
echo ""
echo "When prompted:"
echo "- Username: your GitHub username"
echo "- Password: your Personal Access Token (not your GitHub password)" 