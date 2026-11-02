#!/usr/bin/env node
/**
 * Patches the GitAscii-generated profile SVGs.
 *
 * The GitAscii renderers hardcode a few values that cannot be changed through
 * gitascii.json, so they are corrected here after every render:
 *
 * 1. surveillance-header draws the display name at font-size 48 with
 *    letter-spacing 5. That is ~980px wide for a 29-character name while the
 *    card canvas is only 792px, so the name overflows. Reduce it to 36/1.
 *
 * 2. surveillance-telemetry labels the metric as STARS but fills it with the
 *    number of stars *received* on owned non-fork repos. GitHub's profile
 *    "Stars" tab counts repositories the user has *starred*, so the label is
 *    renamed to STARRED and filled with that count instead.
 *
 * Both rewrites are idempotent: once applied, the search patterns no longer
 * match, so re-running the script is a no-op.
 *
 * Usage: node patch-profile-svg.mjs <directory-with-dark-and-light-svg>
 */

import { readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const NAME_FROM = 'font-size="48" letter-spacing="5"';
const NAME_TO = 'font-size="36" letter-spacing="1"';

const STAR_PATTERN = /(<text[^>]*>)(\d+)(<\/text><text[^>]*>)STARS(<\/text>)/;

const targetDir = resolve(process.argv[2] ?? "profiles/default");

function resolveUsername() {
  const repository = process.env.GITHUB_REPOSITORY;
  if (repository && repository.includes("/")) return repository.split("/")[0];
  return process.argv[3] ?? null;
}

/**
 * Counts repositories the profile owner has starred.
 *
 * Uses the public /users/{name}/starred route rather than /user/starred: inside
 * GitHub Actions GITHUB_TOKEN belongs to the workflow bot, so /user/starred
 * would report the bot's stars instead of the owner's.
 */
async function fetchStarredCount() {
  const username = resolveUsername();
  if (!username) {
    console.warn("[patch] Owner username unknown; cannot resolve starred count.");
    return null;
  }

  const token = process.env.GITHUB_TOKEN;
  const headers = {
    Accept: "application/vnd.github+json",
    "User-Agent": "patch-profile-svg",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  try {
    const response = await fetch(
      `https://api.github.com/users/${encodeURIComponent(username)}/starred?per_page=1`,
      { headers, signal: AbortSignal.timeout(10_000) }
    );

    if (!response.ok) {
      console.warn(`[patch] Starred lookup returned HTTP ${response.status}`);
      return null;
    }

    // per_page=1 keeps the response tiny; the Link header carries the total.
    const link = response.headers.get("link");
    if (link) {
      const lastPage = link.match(/[?&]page=(\d+)>;\s*rel="last"/);
      if (lastPage) return Number(lastPage[1]);
    }

    const body = await response.json();
    return Array.isArray(body) ? body.length : null;
  } catch (error) {
    console.warn(`[patch] Starred lookup failed: ${error.message}`);
    return null;
  }
}

function patchName(svg) {
  const occurrences = svg.split(NAME_FROM).length - 1;
  if (occurrences === 0) {
    return { svg, occurrences, alreadyPatched: svg.includes(NAME_TO) };
  }
  return { svg: svg.split(NAME_FROM).join(NAME_TO), occurrences, alreadyPatched: false };
}

function patchStarredLabel(svg, starredCount) {
  const match = svg.match(STAR_PATTERN);
  if (!match) {
    return { svg, patched: false, alreadyPatched: svg.includes(">STARRED<") };
  }

  const replacement = `$1${starredCount}$3STARRED$4`;
  return { svg: svg.replace(STAR_PATTERN, replacement), patched: true, previous: match[2] };
}

const starredCount = await fetchStarredCount();
if (starredCount === null) {
  console.warn("[patch] Starred count unavailable; leaving the STARS metric untouched.");
}

let failures = 0;

for (const theme of ["dark", "light"]) {
  const file = join(targetDir, `${theme}.svg`);
  const original = await readFile(file, "utf8");

  const nameResult = patchName(original);
  if (nameResult.occurrences === 0) {
    if (nameResult.alreadyPatched) {
      console.log(`[patch] ${theme}.svg: name already resized`);
    } else {
      console.warn(`[patch] ${theme}.svg: name size pattern not found; the GitAscii renderer may have changed.`);
      failures += 1;
    }
  }

  let next = nameResult.svg;

  if (starredCount !== null) {
    const starResult = patchStarredLabel(next, starredCount);
    if (starResult.patched) {
      next = starResult.svg;
      console.log(`[patch] ${theme}.svg: STARS ${starResult.previous} -> STARRED ${starredCount}`);
    } else if (starResult.alreadyPatched) {
      console.log(`[patch] ${theme}.svg: starred metric already relabelled`);
    } else {
      console.warn(`[patch] ${theme}.svg: star metric pattern not found; the GitAscii renderer may have changed.`);
      failures += 1;
    }
  }

  if (next === original) {
    console.log(`[patch] ${theme}.svg: unchanged`);
    continue;
  }

  await writeFile(file, next, "utf8");
  console.log(`[patch] ${theme}.svg: name resized in ${nameResult.occurrences} place(s), file rewritten`);
}

if (failures > 0) {
  console.warn(
    `[patch] ${failures} expected pattern(s) were missing. The GitAscii renderer may have changed; the SVGs were still published.`
  );
}
