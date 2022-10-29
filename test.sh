#!/bin/bash

pushd /opt/blog
git fetch

neec_to_pull=$(git status | grep -i "Your branch is behind")


if [ ! -z "$neec_to_pull" ]; then
    echo "Need to pull"

    # re-build blog
    # sudo rm -rf /opt/blog
    # sudo mkdir -p /opt/blog
    # sudo git clone --branch=gh-pages https://github.com/alecmaly/blog.git /opt/blog
    git pull
    docker run -v "/var/www/html:/var/www/html" -v "$(pwd):/opt/blog" blog /opt/blog/docker_build.sh
    popd 

    # rebuild search index
    pushd /opt/alecmaly.com/services/blog_search_service/
    python3 generate_search_index.py -s /var/www/html/blog
    popd

else
    echo "No action necessary"
fi