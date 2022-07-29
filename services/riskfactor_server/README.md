# Steps to run

```bash
docker-machine env default | Invoke-Expression

# build image
docker image build -t python:riskfactor_proxy .

# run image
docker run -p 8000:8000 python:riskfactor_proxy

echo "http://$(docker-machine ip):8000/?q=Yadkinville%2cNC&type=flood"
```