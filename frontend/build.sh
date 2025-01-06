#!/bin/bash

#compile tailwind
npx tailwindcss -i ../static/input.css -o ./src/output.css

# Build the frontend
tsc && vite build

find ./dist/assets/ -type f -name 'index*.js' -exec mv {} ./dist/assets/index.js \;
find ./dist/assets/ -type f -name 'index*.css' -exec mv {} ./dist/assets/index.css \;

# Copy the compiled frontend to be rendered by the backend
mv ./dist/assets/index.js ../static/index.js
mv ./dist/assets/index.css ../static/index.css
cp -p ./src/output.css ../static/output.css