# Info

Blog is built in the ./blog directory, output goes to /var/www/html/blog
/var/www/html/blog is used as a volume in the nginx server and .html files are hosted

# Run it

```powershell
docker-machine env default | Invoke-Expression
docker-compose up

docker-machine ip
```


# BLOG SETUP

- https://elternativeht.github.io/2019/04/operations-on-vps/

## setup
```bash
sudo apt update && apt upgrade -y

apt install -y jq
```

Make /blog directory and clone blog repo 
```
mkdir blog
cd ./blog
git clone --branch gh-pages https://github.com/alecmaly/blog.git /opt/blog

# install requirements for building search index
sudo apt update && sudo apt install python3-pip
pip3 install -r /opt/alecmaly.com/services/blog_search_service/requirements.txt
```

## build
```bash
## rebuild image
# docker build -t blog .
cd blog

# build blog using container
rm -rf /var/www/html/blog
mkdir -p /var/www/html/blog
docker run -v "/var/www/html:/var/www/html" -v "$(pwd):/opt/blog" blog /opt/blog/docker_build.sh

cd ..
```

