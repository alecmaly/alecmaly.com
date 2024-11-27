FROM node:latest

WORKDIR /app

COPY . .

# run apt update
RUN apt-get update && apt-get install -y 
RUN npm install

EXPOSE 80

CMD ["node", "server.js"]