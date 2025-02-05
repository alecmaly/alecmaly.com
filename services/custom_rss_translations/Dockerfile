FROM node:latest

WORKDIR /app

RUN apt-get update && apt-get install -y 

COPY . .
RUN npm install

EXPOSE 80

CMD ["node", "server.js"]