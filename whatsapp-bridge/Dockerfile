FROM node:20-alpine

WORKDIR /app

# Copier package.json
COPY package*.json ./

# Installer les dépendances
RUN npm install 

# Copier le code
COPY . .

# Port
EXPOSE 3500

# Démarrer
CMD ["node", "whatsapp-bridge.js"]