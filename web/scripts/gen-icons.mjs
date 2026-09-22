/** Генерация PWA-иконок из design/assets/logo-b.svg (белая b на меди).
 * Запуск: npm run gen-icons. Выход: public/icons/*.png
 */
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const out = join(root, "public", "icons");
mkdirSync(out, { recursive: true });

const mark = readFileSync(join(root, "..", "design", "assets", "logo-b.svg"), "utf-8");

function svg(size, bg, fg, pad) {
  const inner = size - pad * 2;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
<rect width="${size}" height="${size}" rx="${size * 0.22}" fill="${bg}"/>
<g transform="translate(${pad} ${pad}) scale(${inner / 100})" color="${fg}">${mark.replace(/<svg[^>]*>|<\/svg>/g, "")}</g>
</svg>`;
}

const jobs = [
  ["icon-192.png", 192, "#c58c67", "#f7ede4", 34, false],
  ["icon-512.png", 512, "#c58c67", "#f7ede4", 90, false],
  ["maskable-512.png", 512, "#c58c67", "#f7ede4", 120, false],
  ["apple-touch-icon.png", 180, "#0c0a09", "#f3d8c3", 32, false],
];

for (const [file, size, bg, fg, pad] of jobs) {
  const buf = Buffer.from(svg(size, bg, fg, pad));
  await sharp(buf).png().toFile(join(out, file));
  console.log("wrote", file);
}
