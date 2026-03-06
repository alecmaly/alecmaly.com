#!/bin/bash

# Setup (run once):
#   # Install nvm
#   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
#   source ~/.bashrc
#
#   # Install Node.js
#   nvm install 22
#   nvm use 22
#
#   # If using private repo, set up SSH key for GitHub
#   ssh-keygen -t rsa -b 4096
#   # Upload public key to GitHub: https://github.com/settings/keys
#
#   # Set up cron job
#   # crontab -e
#   # */5 * * * * /opt/alecmaly.com/rebuild_blog.sh >> /var/log/rebuild_blog.log 2>&1
#
# Usage:
#   ./rebuild_blog.sh         # Normal operation (only rebuild if changes detected)
#   ./rebuild_blog.sh --force # Force rebuild regardless of git status

GITHUB_USER="alecmaly"
# env variable
# export GITHUB_TOKEN="" # read to contents of blog. not super sensitive, fine with hardcoded credentials


# Check for --force flag
FORCE_REBUILD=false
if [ "$1" = "--force" ]; then
    FORCE_REBUILD=true
    echo "Force rebuild requested"
fi

source /etc/secure_env

# create /opt/blog as sudo
sudo mkdir -p /opt/blog

# grant permissions to user `ubuntu`
sudo chown -R ubuntu:ubuntu /opt/blog

# grant permissions to user `ubuntu`
sudo chmod -R 755 /opt/blog

# Check git status as ubuntu user
need_to_pull=$(sudo -u ubuntu bash -c "cd /opt/blog && git fetch && git status 2>&1" | grep -iE "(Your branch is behind|not a git repository)")

if [ ! -z "$need_to_pull" ] || [ "$FORCE_REBUILD" = true ]; then
    echo "Need to pull"

    # Clean
    sudo cd /opt
    sudo rm -rf /opt/blog
    sudo mkdir -p /opt/blog

    # grant permissions to user `ubuntu`
    sudo chown -R ubuntu:ubuntu /opt/blog

    # clone as ubuntu user
    sudo -u ubuntu GITHUB_USER=$GITHUB_USER GITHUB_TOKEN=$GITHUB_TOKEN git clone --branch main "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/alecmaly/blog.git" /opt/blog

    # Build as ubuntu user
    sudo -u ubuntu bash -c "source ~/.nvm/nvm.sh && cd /opt/blog && npm ci && npm run build"

    # Copy built files as root (since /var/www/html needs root permissions)
    rm -rf /var/www/html/blog/*
    mkdir -p /var/www/html/blog
    cp -r /opt/blog/dist/* /var/www/html/blog/
    
    # Ensure ubuntu can read the files
    chown -R ubuntu:ubuntu /var/www/html/blog
    chmod -R 755 /var/www/html/blog
else
    echo "No action necessary"
fi
