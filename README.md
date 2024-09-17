
# Project Info

Blog is built in the ./blog directory, output goes to /var/www/html/blog
/var/www/html/blog is used as a volume in the nginx server and .html files are hosted

## Dependencies

- docker / docker-machine

# Run it

```powershell
docker-machine env default | Invoke-Expression
docker-compose up

docker-machine ip
```

# Setup: alecmaly.com
```bash
git clone https://github.com/alecmaly/alecmaly.com /opt/alecmaly.com
cd /opt/alecmaly.com

# install requirements for building search index
sudo apt update && sudo apt install python3-pip
pip3 install -r /opt/alecmaly.com/services/blog_search_service/requirements.txt
```

# Setup: SharePoint JSON Formatter

## Dependencies
```bash
git clone https://github.com/alecmaly/sharepoint-json-helper.git /opt/sharepoint-json-helper
cd /opt/sharepoint-json-helper

docker build --rm -f Dockerfile -t alecmaly/sharepoint-json-helper .
```


# Setup: Random Info Website

## Dependencies
```bash
git clone https://github.com/alecmaly/random-info-website.git 
cd /opt/random-info-website

docker build --rm -f Dockerfile -t alecmaly/random-info-website .
```


# Setup: Blog

- https://elternativeht.github.io/2019/04/operations-on-vps/

## Dependencies
```bash
sudo apt update && apt upgrade -y

apt install -y jq
```

Make /blog directory and clone blog repo 
```bash
# mkdir /opt/blog
# cd /opt/blog
git clone --branch gh-pages https://github.com/alecmaly/blog.git /opt/blog
cd /opt/blog
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

<br>
<br><hr>
<br>

# Upgrade requirements.txt

```shell
# python venv
pip install pip-upgrader
pip-upgrade path/to/requirements.txt
```
