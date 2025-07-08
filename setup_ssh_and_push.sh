#!/bin/bash

# Navigate to the project directory
cd "/Users/aayushkher/Desktop/project plumber"

echo "Setting up SSH authentication for GitHub..."

# Check if SSH keys exist
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "SSH key not found. Generating new SSH key..."
    ssh-keygen -t rsa -b 4096 -C "your_email@example.com" -f ~/.ssh/id_rsa -N ""
    echo "SSH key generated successfully!"
else
    echo "SSH key already exists."
fi

# Start ssh-agent and add the key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa

# Display the public key
echo "Your SSH public key is:"
echo "=========================================="
cat ~/.ssh/id_rsa.pub
echo "=========================================="
echo ""
echo "Please copy this key and add it to your GitHub account:"
echo "1. Go to GitHub.com and sign in"
echo "2. Click your profile picture → Settings"
echo "3. Click 'SSH and GPG keys' in the sidebar"
echo "4. Click 'New SSH key'"
echo "5. Paste the key above and save"
echo ""
echo "After adding the key to GitHub, press Enter to continue..."
read -p "Press Enter when you've added the SSH key to GitHub..."

# Change remote URL to use SSH
echo "Changing remote URL to use SSH..."
git remote set-url origin git@github.com:Aayushhkher/plumbing.git

# Test SSH connection
echo "Testing SSH connection to GitHub..."
ssh -T git@github.com

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main

echo "Done!" 