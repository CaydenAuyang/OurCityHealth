#!/bin/bash
cd frontend

# Nuke caches
rm -rf node_modules package-lock.json .vite

# Reinstall
npm install

# Verify config existence
if [ ! -f tailwind.config.js ]; then
    echo "Creating tailwind config..."
    npx tailwindcss init -p
fi

# Run
npm run dev
