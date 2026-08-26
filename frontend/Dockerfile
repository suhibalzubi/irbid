# Dockerfile for frontend
FROM node:18-alpine
WORKDIR /usr/src/app
COPY frontend/package.json /usr/src/app/package.json
RUN npm install
COPY frontend /usr/src/app
EXPOSE 3000
CMD ["npm", "start"]
