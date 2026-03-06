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
GITHUB_TOKEN="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" # read to contents of blog. not super sensitive, fine with hardcoded credentials


# Check for --force flag
FORCE_REBUILD=false
if [ "$1" = "--force" ]; then
    FORCE_REBUILD=true
    echo "Force rebuild requested"
fi


# create /opt/blog as sudo
sudo mkdir -p /opt/blog

# grant permissions to user `ubuntu`
sudo chown -R ubuntu:ubuntu /opt/blog

# grant permissions to user `ubuntu`
sudo chmod -R 755 /opt/blog

# drop into user ubuntu shell for rest of commands
sudo -u ubuntu -i

pushd /opt/blog
git fetch
need_to_pull=$(git status 2>&1 | grep -iE "(Your branch is behind|not a git repository)")
popd

if [ ! -z "$need_to_pull" ] || [ "$FORCE_REBUILD" = true ]; then
    echo "Need to pull"

    rm -rf /opt/blog
    mkdir -p /opt/blog
    # git clone --branch=main git@github.com:alecmaly/blog.git /opt/blog
    git clone --branch main "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/alecmaly/blog.git" /opt/blog

    cd /opt/blog
    npm ci
    npm run build

    rm -rf /var/www/html/blog/*
    mkdir -p /var/www/html/blog
    cp -r dist/* /var/www/html/blog/
else
    echo "No action necessary"
fi
