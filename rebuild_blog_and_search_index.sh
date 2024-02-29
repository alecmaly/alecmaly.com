#!/bin/bash

# # install dependencies
# sudo apt update && sudo apt install python3-pip
# pip3 install -r /opt/alecmaly.com/services/blog_search_service/requirements.txt

# these may be needed for github auth
# - if broken, regenerate key `ssh-keygen -t rsa -b 4096 ` + upload public key to GitHub
eval "$(ssh-agent -s)" > /tmp/ssh_agent_output
SSH_AGENT_PID=`cat /tmp/ssh_agent_output | cut -d' ' -f3`
rm /tmp/ssh_agent_output
ssh-add ~/.ssh/id_rsa


pushd /opt/blog
git fetch
need_to_pull=$(git status 2>&1 | grep -iE "(Your branch is behind|not a git repository)")
popd

if [ ! -z "$need_to_pull" ]; then
    echo "Need to pull"
    
    # re-build blog
    sudo rm -rf /opt/blog
    sudo mkdir -p /opt/blog
    sudo git clone --branch=gh-pages git@github.com:alecmaly/blog.git /opt/blog
    
    pushd /opt/blog
    # build tags
    python3 tag_generator.py 

    docker run -v "/var/www/html:/var/www/html" -v "$(pwd):/opt/blog" blog /opt/blog/docker_build.sh
    popd 

    # rebuild search index
    pushd /opt/alecmaly.com/services/blog_search_service/
    python3 generate_search_index.py -s /var/www/html/blog
    popd
else
    echo "No action necessary"
fi

echo "killing id: $SSH_AGENT_PID"
# Kill ssh-agent process
kill $SSH_AGENT_PID
