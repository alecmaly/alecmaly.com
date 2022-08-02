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
git clone --branch gh-pages https://github.com/alecmaly/blog.git
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
