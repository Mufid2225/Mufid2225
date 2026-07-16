import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import sharp from "sharp";

const root = resolve(import.meta.dirname, "..");
const output = resolve(root, "assets/hero");
const portraitColumns = 84;
const portraitRows = 84;
const { data: portraitPixels } = await sharp(resolve(root, "assets/portrait-cutout.png"))
  .resize(portraitColumns, portraitRows, { fit: "fill" })
  .ensureAlpha()
  .raw()
  .toBuffer({ resolveWithObject: true });

const portraitLuminance = [];
for (let offset = 0; offset < portraitPixels.length; offset += 4) {
  const [red, green, blue, alpha] = portraitPixels.subarray(offset, offset + 4);
  if (alpha >= 105) portraitLuminance.push((red * 0.2126 + green * 0.7152 + blue * 0.0722) / 255);
}
portraitLuminance.sort((a, b) => a - b);
const luminanceLow = portraitLuminance[Math.floor(portraitLuminance.length * 0.02)];
const luminanceHigh = portraitLuminance[Math.floor(portraitLuminance.length * 0.98)];

const themes = {
  dark: {
    bg: "#050914", panel: "#08111f", text: "#e6edf7", muted: "#718096",
    cyan: "#22d3ee", blue: "#3b82f6", orange: "#fb923c", grid: "#17304c",
    photoBlend: "screen", photoOpacity: 0.9,
  },
  light: {
    bg: "#f4f8fb", panel: "#ffffff", text: "#142033", muted: "#64748b",
    cyan: "#0891b2", blue: "#2563eb", orange: "#ea580c", grid: "#bfd3df",
    photoBlend: "multiply", photoOpacity: 0.82,
  },
};

const escape = (value) => value.replaceAll("&", "&amp;").replaceAll("<", "&lt;");

function asciiPortrait(frame, colors, mobile) {
  const cellSize = mobile ? 4.05 : 5.15;
  const fontSize = mobile ? 4.75 : 6;
  const totalWidth = portraitColumns * cellSize;
  const totalHeight = portraitRows * cellSize;
  const startX = frame.x + (frame.w - totalWidth) / 2;
  const startY = frame.y + (frame.h - totalHeight) / 2;
  const ramp = ".:-=+*#%@";
  const segments = [];

  for (let row = 0; row < portraitRows; row++) {
    let segmentStart = -1;
    let characters = "";

    const flushSegment = () => {
      if (segmentStart === -1) return;
      const x = startX + segmentStart * cellSize;
      const y = startY + (row + 0.82) * cellSize;
      const width = characters.length * cellSize;
      const color = row % 5 === 0 ? colors.cyan : colors.blue;
      segments.push(`<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" textLength="${width.toFixed(1)}" lengthAdjust="spacing" fill="${color}" opacity=".94">${characters}</text>`);
      segmentStart = -1;
      characters = "";
    };

    for (let column = 0; column < portraitColumns; column++) {
      const offset = (row * portraitColumns + column) * 4;
      const [red, green, blue, alpha] = portraitPixels.subarray(offset, offset + 4);
      if (alpha < 105) {
        flushSegment();
        continue;
      }
      const luminance = (red * 0.2126 + green * 0.7152 + blue * 0.0722) / 255;
      const normalized = Math.max(0, Math.min(1, (luminance - luminanceLow) / (luminanceHigh - luminanceLow)));
      const contrast = normalized ** 0.82;
      const character = ramp[Math.round(contrast * (ramp.length - 1))];
      if (segmentStart === -1) segmentStart = column;
      characters += character;
    }
    flushSegment();
  }

  return `<g class="ascii-portrait" font-family="'Courier New',monospace" font-size="${fontSize}" font-weight="700">${segments.join("")}</g>`;
}

function rows(items, x, y, width, lineHeight, colors) {
  return items.map((item, index) => {
    const yy = y + index * lineHeight;
    if (item.section) {
      const lineStart = x + item.section.length * 8.4 + 18;
      return `<text x="${x}" y="${yy}" class="section">${escape(item.section)}</text><line x1="${lineStart}" y1="${yy - 4}" x2="${x + width}" y2="${yy - 4}" stroke="${colors.cyan}" opacity=".55"/>`;
    }
    if (item.blank) return "";
    return `<text x="${x}" y="${yy}" class="row"><tspan class="key">${escape(item.key)}</tspan><tspan class="dots">  ${".".repeat(Math.max(3, 13 - item.key.length))}  </tspan><tspan>${escape(item.value)}</tspan></text>`;
  }).join("\n");
}

function svg(themeName, mobile) {
  const c = themes[themeName];
  const W = mobile ? 720 : 1200;
  const H = mobile ? 1120 : 620;
  const photo = mobile
    ? { x: 42, y: 92, w: 636, h: 370 }
    : { x: 28, y: 82, w: 475, h: 470 };
  const info = mobile
    ? { x: 42, y: 490, w: 636, h: 552, tx: 68, ty: 535, line: 25, rw: 550 }
    : { x: 528, y: 82, w: 644, h: 470, tx: 558, ty: 127, line: 23, rw: 575 };
  const revealStepCount = 20;
  const infoRevealValues = Array.from({ length: revealStepCount }, (_, index) => Math.round(info.h * index / (revealStepCount - 1))).join(";");
  const infoRevealTimes = Array.from({ length: revealStepCount }, (_, index) => (index / (revealStepCount - 1)).toFixed(3)).join(";");
  const scanTravel = H - 176;
  const items = [
    { key: "Name", value: "Muhammad Mufid Arhaburrizqi" },
    { key: "Role", value: "AI & Automation Enthusiast" },
    { key: "Education", value: "SMKN 2 Singosari" },
    { key: "Current", value: "Intern at JV. Partner Indonesia" },
    { key: "Status", value: "Software Engineering / Internship" },
    { blank: true },
    { section: "FOCUS.STREAM" },
    { key: "Primary", value: "AI Agents & LLM Workflows" },
    { key: "Build", value: "Full Stack Web Development" },
    { blank: true },
    { section: "TOOLCHAIN" },
    { key: "Core", value: "TypeScript / JavaScript / Next.js" },
    { key: "Systems", value: "Tailwind CSS / Docker / Git" },
    { blank: true },
    { section: "NETWORK" },
    { key: "GitHub", value: "@Mufid2225" },
    { key: "Portfolio", value: "mufid-homepage.dedyn.io" },
  ];

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="title desc">
  <title id="title">Muhammad Mufid Arhaburrizqi - AI and Automation Enthusiast</title>
  <desc id="desc">Developer profile presented as an automation control room.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${c.bg}"/><stop offset="1" stop-color="${c.panel}"/></linearGradient>
    <linearGradient id="edge"><stop stop-color="${c.orange}"/><stop offset=".45" stop-color="${c.cyan}"/><stop offset="1" stop-color="${c.blue}"/></linearGradient>
    <linearGradient id="scanBeam" x1="0" y1="0" x2="0" y2="1"><stop stop-color="${c.cyan}" stop-opacity="0"/><stop offset=".4" stop-color="${c.cyan}" stop-opacity=".04"/><stop offset=".49" stop-color="${c.cyan}" stop-opacity=".2"/><stop offset=".5" stop-color="${c.cyan}" stop-opacity=".48"/><stop offset=".51" stop-color="${c.cyan}" stop-opacity=".2"/><stop offset=".6" stop-color="${c.cyan}" stop-opacity=".04"/><stop offset="1" stop-color="${c.cyan}" stop-opacity="0"/></linearGradient>
    <clipPath id="portraitClip"><rect x="${photo.x}" y="${photo.y}" width="${photo.w}" height="${photo.h}" rx="14"/></clipPath>
    <clipPath id="portraitReveal"><rect x="${photo.x}" y="${photo.y}" width="${photo.w}" height="0"><animate attributeName="height" from="0" to="${photo.h}" dur="2.2s" begin=".35s" fill="freeze"/></rect></clipPath>
    <clipPath id="infoReveal"><rect x="${info.x}" y="${info.y}" width="${info.w}" height="0"><animate attributeName="height" values="${infoRevealValues}" keyTimes="${infoRevealTimes}" calcMode="discrete" dur="3.6s" begin="1s" fill="freeze"/></rect></clipPath>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="${c.grid}" stroke-width="1" opacity=".28"/></pattern>
    <style>
      .mono{font-family:'Courier New',monospace}.micro{font:11px 'Courier New',monospace;letter-spacing:2px;fill:${c.muted}}.label{font:12px 'Courier New',monospace;letter-spacing:2px;fill:${c.cyan}}.row{font:14px 'Courier New',monospace;fill:${c.text}}.key,.section{font-weight:700;fill:${c.cyan}}.dots{fill:${c.muted}}.section{font:13px 'Courier New',monospace;letter-spacing:1px}
    </style>
  </defs>
  <rect width="${W}" height="${H}" rx="20" fill="url(#bg)"/>
  <rect x="2" y="2" width="${W - 4}" height="${H - 4}" rx="18" fill="none" stroke="url(#edge)" stroke-width="2"/>
  <rect x="1" y="42" width="${W - 2}" height="1" fill="${c.grid}"/>
  <circle cx="22" cy="22" r="5" fill="#ef4444"/><circle cx="40" cy="22" r="5" fill="#f59e0b"/><circle cx="58" cy="22" r="5" fill="#10b981"/>
  <text x="${W / 2}" y="27" text-anchor="middle" class="micro">mufid@automation-lab ~ $ ./build-future --ship</text>
  <circle cx="${W - 104}" cy="22" r="4" fill="${c.orange}"><animate attributeName="opacity" values="1;.25;1" dur="1.7s" repeatCount="indefinite"/></circle>
  <text x="${W - 92}" y="26" class="micro" style="fill:${c.orange}">ONLINE</text>

  <text x="${photo.x + 10}" y="${photo.y - 10}" class="label">PORTRAIT.FEED / HUMAN.SIGNAL</text>
  <rect x="${photo.x}" y="${photo.y}" width="${photo.w}" height="${photo.h}" rx="14" fill="${c.panel}" stroke="${c.cyan}" opacity=".9"/>
  <g clip-path="url(#portraitClip)">
    <rect x="${photo.x}" y="${photo.y}" width="${photo.w}" height="${photo.h}" fill="url(#grid)"/>
    <g clip-path="url(#portraitReveal)">${asciiPortrait(photo, c, mobile)}</g>
  </g>
  <path d="M${photo.x + 18} ${photo.y + 45}V${photo.y + 18}H${photo.x + 58} M${photo.x + photo.w - 18} ${photo.y + photo.h - 45}V${photo.y + photo.h - 18}H${photo.x + photo.w - 58}" fill="none" stroke="${c.orange}" stroke-width="2"/>

  <text x="${info.x + 16}" y="${info.y - 10}" class="label">SYSTEM.INFO / BUILDER.PROFILE</text>
  <rect x="${info.x}" y="${info.y}" width="${info.w}" height="${info.h}" rx="14" fill="${c.panel}" fill-opacity=".5" stroke="${c.blue}" opacity=".9"/>
  <g clip-path="url(#infoReveal)">
    <text x="${info.tx}" y="${info.ty - 22}" class="mono" font-size="17" font-weight="700" fill="${c.orange}">MUFID@AUTOMATION-LAB</text>
    ${rows(items, info.tx, info.ty + 8, info.rw, info.line, c)}
    <text x="${info.tx}" y="${info.y + info.h - 20}" class="mono" font-size="13" fill="${c.cyan}"><tspan>▋</tspan> signal.ready &gt; LEARN / BUILD / AUTOMATE</text>
  </g>
  <text x="${W / 2}" y="${H - 20}" text-anchor="middle" class="micro">AI AGENTS / WEB SYSTEMS / CONTINUOUS LEARNING</text>
  <g pointer-events="none" style="mix-blend-mode:${c.scanBlend}">
    <rect x="2" y="43" width="${W - 4}" height="110" fill="url(#scanBeam)"/>
    <line x1="2" y1="98" x2="${W - 2}" y2="98" stroke="${c.cyan}" stroke-width="1.5" opacity=".5"/>
    <animateTransform attributeName="transform" type="translate" values="0 0;0 ${scanTravel};0 0" dur="7.5s" repeatCount="indefinite"/>
  </g>
</svg>`;
}

await mkdir(output, { recursive: true });
for (const theme of Object.keys(themes)) {
  await writeFile(resolve(output, `mufid-console-${theme}.svg`), svg(theme, false));
  await writeFile(resolve(output, `mufid-console-mobile-${theme}.svg`), svg(theme, true));
}
console.log("Generated four responsive profile hero SVGs.");
