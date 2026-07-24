#!/usr/bin/env python3
"""Post-process Bomberman SVG: remove Player 2, all bombs, keep Player 1 alive and walking."""

import re, sys


def fix_bomberman_svg(svg: str) -> str:
    # ── Player 2 removal ──
    # Remove Player 2 sprite symbols
    svg = re.sub(r'<symbol id="bm-player-2-[^"]*"[^>]*>.*?</symbol>', '', svg, flags=re.DOTALL)
    # Remove Player 2 death symbols
    svg = re.sub(r'<symbol id="bm-player-2-death-[^"]*"[^>]*>.*?</symbol>', '', svg, flags=re.DOTALL)
    # Remove Player 2 use element
    svg = re.sub(r'<use id="player-2"[^>]*>.*?</use>', '', svg, flags=re.DOTALL)

    # ── Remove ALL bombs ──
    svg = re.sub(r'<g id="bomb-\d+"[^>]*>.*?</g>', '', svg, flags=re.DOTALL)

    # ── Remove ALL explosion shapes (bm-explosion-shape-*) ──
    # These are defined as <g> elements in <defs> and referenced by explosions
    svg = re.sub(r'<g id="bm-explosion-shape-[^"]*"[^>]*>.*?</g>', '', svg, flags=re.DOTALL)

    # ── Fix Player 1 ──
    def fix_p1(m):
        block = m.group(0)

        # Fix href: remove death sprite references
        # Find current keyTimes and values
        href_match = re.search(r'<animate attributeName="href"[^>]*keyTimes="([^"]+)"[^>]*values="([^"]+)"', block)
        if href_match:
            vals = href_match.group(2).split(';')
            # Find first death sprite index
            death_idx = next((i for i, v in enumerate(vals) if 'death' in v), len(vals))
            if death_idx < len(vals):
                # Truncate to before death, add looping frames
                good_vals = vals[:death_idx]
                good_times = href_match.group(1).split(';')[:death_idx]
                # Make last keyTime = 1 and fill remaining with walking frames
                good_vals.extend([good_vals[-1]] * 3)
                good_times = [str(round(i * 0.99 / max(len(good_vals) - 1, 1), 6)) for i in range(len(good_vals) - 1)] + ['1']
                # Pad keyTimes to match values count
                while len(good_times) < len(good_vals):
                    good_times.append('1')

                block = re.sub(
                    r'keyTimes="[^"]+"',
                    f'keyTimes="{";".join(good_times)}"',
                    block,
                    count=1,
                )
                block = re.sub(
                    r'values="[^"]+"',
                    f'values="{";".join(good_vals)}"',
                    block,
                    count=1,
                )

        # Fix opacity: always 1 (no death)
        block = re.sub(
            r'<animate attributeName="opacity"[^>]*keyTimes="[^"]*"[^>]*values="[^"]*"',
            '<animate attributeName="opacity" calcMode="discrete" dur="5400ms" repeatCount="indefinite" keyTimes="0;1" values="1;1"/>',
            block,
        )

        return block

    svg = re.sub(r'<use id="player-1"[^>]*>.*?</use>', fix_p1, svg, flags=re.DOTALL)

    # Clean up empty lines
    svg = re.sub(r'\n\s*\n', '\n', svg)

    return svg


def main():
    if len(sys.argv) < 2:
        print('Usage: fix_bomberman.py <svg_file> [svg_file2 ...]')
        sys.exit(1)

    for path in sys.argv[1:]:
        with open(path, 'r', encoding='utf-8') as f:
            svg = f.read()

        fixed = fix_bomberman_svg(svg)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(fixed)

        orig_kb = len(svg) / 1024
        new_kb = len(fixed) / 1024
        print(f'{path}: {orig_kb:.1f}KB -> {new_kb:.1f}KB')


if __name__ == '__main__':
    main()
