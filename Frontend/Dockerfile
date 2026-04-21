FROM node:16-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
RUN npm install

# Copy the application code
COPY . .

# Expose the port
EXPOSE 3000

# Run the application
CMD ["npm", "run", "dev"]
