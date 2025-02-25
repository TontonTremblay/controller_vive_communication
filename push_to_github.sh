#!/bin/bash

echo "Pushing HTC Vive Controller Tracker to GitHub..."

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed."
    echo "Please install Git using your package manager."
    echo "For example: sudo apt install git (Ubuntu/Debian)"
    echo "             sudo yum install git (CentOS/RHEL)"
    echo "             brew install git (macOS with Homebrew)"
    exit 1
fi

# Check if repository is already initialized
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
    
    # Configure Git if needed
    echo "Please enter your Git username:"
    read GIT_USERNAME
    git config user.name "$GIT_USERNAME"
    
    echo "Please enter your Git email:"
    read GIT_EMAIL
    git config user.email "$GIT_EMAIL"
fi

# Add all files
echo "Adding files to repository..."
git add .

# Commit changes
echo "Committing changes..."
git commit -m "Initial commit: HTC Vive Controller Tracker"

# Check if remote already exists
if ! git remote | grep -q "origin"; then
    echo "Adding remote repository..."
    git remote add origin git@github.com:TontonTremblay/controller_vive_communication.git
fi

# Determine default branch (main or master)
echo "Checking default branch..."
if git branch | grep -q "main"; then
    BRANCH="main"
else
    BRANCH="master"
fi

# Push to GitHub
echo "Pushing to GitHub (branch: $BRANCH)..."
git push -u origin $BRANCH

echo
if [ $? -eq 0 ]; then
    echo "Successfully pushed to GitHub!"
else
    echo "Failed to push to GitHub."
    echo
    echo "Possible issues:"
    echo "1. SSH key not set up for GitHub"
    echo "2. Repository already exists and has different history"
    echo "3. Network connectivity issues"
    echo
    echo "For SSH key setup, visit: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"
fi

echo
read -p "Press Enter to continue..." 