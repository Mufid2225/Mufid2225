#!/usr/bin/env python3
"""Post-process Bomberman SVG: remove Player 2, keep Player 1 alive."""

import re, sys, os


def fix_bomberman_svg(svg: str) -> str:
    # 1. Remove Player 2 sprite symbols
    svg = re.sub(
        r'<symbol id="bm-player-2-[^"]*"[^>]*>.*?</symbol>',
        '',
        svg,
        flags=re.DOTALL,
    )

    # 2. Remove Player 2 death symbols
    svg = re.sub(
        r'<symbol id="bm-player-2-death-[^"]*"[^>]*>.*?</symbol>',
        '',
        svg,
        flags=re.DOTALL,
    )

    # 3. Remove Player 2 use element entirely
    svg = re.sub(
        r'<use id="player-2"[^>]*>.*?</use>',
        '',
        svg,
        flags=re.DOTALL,
    )

    # 5. Remove Player 2's animateTransform (second one, finds by position)
    # Find all animateTransform and take only the one for player-1
    # But easier: remove the second animateTransform after removing player-2 use

    # 6. Fix Player 1 href animation: remove death sprites from values
    def fix_p1_href(m):
        full = m.group(0)
        # Find the values attribute
        inner = full
        # Remove death sprite values from the values string
        # Only keep keyTimes/values before death
        inner = re.sub(
            r'(keyTimes="[^"]*0\.8679[^"]*")',
            'keyTimes="0;0.0377;0.0755;0.1132;0.1509;0.1887;0.2264;0.2642;0.3019;0.3396;0.3774;0.4151;0.4528;0.4906;0.5283;0.5472;0.566;0.5849;0.6038;0.717;0.7358;0.7547;0.7736;0.7925;1"',
            inner,
        )
        inner = re.sub(
            r'values="[^"]*bm-player-1-death[^"]*"',
            'values="#bm-player-1-right-0;#bm-player-1-right-1;#bm-player-1-right-2;#bm-player-1-right-3;#bm-player-1-right-4;#bm-player-1-right-5;#bm-player-1-right-0;#bm-player-1-right-1;#bm-player-1-right-2;#bm-player-1-right-3;#bm-player-1-right-4;#bm-player-1-right-5;#bm-player-1-right-0;#bm-player-1-right-1;#bm-player-1-right-2;#bm-player-1-down-2;#bm-player-1-down-3;#bm-player-1-up-3;#bm-player-1-up-0;#bm-player-1-left-1;#bm-player-1-down-3;#bm-player-1-down-0;#bm-player-1-left-2;#bm-player-1-left-0;#bm-player-1-right-1;#bm-player-1-right-2"',
            inner,
        )
        return inner

    svg = re.sub(
        r'<use id="player-1"[^>]*>.*?</use>',
        fix_p1_href,
        svg,
        flags=re.DOTALL,
    )

    # Clean up empty lines from removed elements
    svg = re.sub(r'\n\s*\n', '\n', svg)

    return svg


def main():
    if len(sys.argv) < 2:
        print('Usage: fix_bomberman.py <svg_file>')
        sys.exit(1)

    path = sys.argv[1]
    with open(path, 'r', encoding='utf-8') as f:
        svg = f.read()

    fixed = fix_bomberman_svg(svg)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(fixed)

    orig_size = len(svg) / 1024
    new_size = len(fixed) / 1024
    print(f'{path}: {orig_size:.1f}KB -> {new_size:.1f}KB')


if __name__ == '__main__':
    main()