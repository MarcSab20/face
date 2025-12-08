FROM node:18-alpine

WORKDIR /app

# Copier package.json
COPY package*.json ./

# Installer les dépendances
RUN npm install --production

# Copier le code
COPY . .

# Port
EXPOSE 3500

# Démarrer
CMD ["node", "whatsapp-bridge.js"]