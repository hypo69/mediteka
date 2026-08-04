// create-icons.js
// Run: node create-icons.js
// Requires: npm install canvas

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

const sizes = [16, 48, 128];

for (const size of sizes) {
    const canvas = createCanvas(size, size);
    const ctx = canvas.getContext('2d');

    // Фон
    ctx.fillStyle = '#1a73e8';
    ctx.beginPath();
    ctx.roundRect(0, 0, size, size, size * 0.2);
    ctx.fill();

    // Буква A
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.round(size * 0.6)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('A', size / 2, size / 2);

    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(path.join(__dirname, 'icons', `icon${size}.png`), buffer);
    console.log(`Created icon${size}.png`);
}
