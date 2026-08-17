FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --include=dev

ARG VITE_AUTH_API_URL
ARG VITE_AI_API_URL

ENV VITE_AUTH_API_URL=$VITE_AUTH_API_URL
ENV VITE_AI_API_URL=$VITE_AI_API_URL

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]