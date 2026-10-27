// Night skyline for the hero: plain SVG paths generated from a fixed seed, so every visit sees the
// same city.

export interface Skyline {
  far: string;
  near: string;
  windows: { x: number; y: number; lit: boolean }[];
  signs: { x: number; y: number; height: number }[];
}

const WIDTH = 1440;
export const CITY_HEIGHT = 300;

function random(seed: number) {
  let state = seed;
  return () => {
    state = (state * 16807) % 2147483647;
    return state / 2147483647;
  };
}

type Point = [number, number];

function toPath(points: Point[]): string {
  return "M" + points.map((point) => point.join(" ")).join("L") + "Z";
}

/** One row of buildings with flat, stepped, slanted, antenna and tower roofs. */
function buildings(next: () => number, minHeight: number, maxHeight: number) {
  const shapes: Point[][] = [];
  const blocks: { x: number; right: number; top: number }[] = [];
  const base = CITY_HEIGHT;
  let x = -10;
  while (x < WIDTH + 10) {
    const width = Math.round(36 + next() * 84);
    const top = Math.round(base - (minHeight + next() * (maxHeight - minHeight)));
    const right = x + width;
    const roof = Math.floor(next() * 5);
    const at = (share: number) => Math.round(x + width * share);
    if (roof === 1) {
      const [a, b, low] = [at(0.2), at(0.8), top + 22];
      shapes.push([
        [x, base],
        [x, low],
        [a, low],
        [a, top],
        [b, top],
        [b, low],
        [right, low],
        [right, base],
      ]);
    } else if (roof === 2) {
      shapes.push([
        [x, base],
        [x, top + 26],
        [right, top],
        [right, base],
      ]);
    } else if (roof === 4) {
      const [a, b, low] = [at(0.35), at(0.65), top + 14];
      shapes.push([
        [x, base],
        [x, low],
        [a, low],
        [a, top - 18],
        [b, top - 18],
        [b, low],
        [right, low],
        [right, base],
      ]);
    } else {
      shapes.push([
        [x, base],
        [x, top],
        [right, top],
        [right, base],
      ]);
      if (roof === 3) {
        const mid = at(0.5);
        shapes.push([
          [mid - 1, top],
          [mid - 1, top - 46],
          [mid + 1, top - 46],
          [mid + 1, top],
        ]);
      }
    }
    blocks.push({ x, right, top });
    x = right + Math.round(next() * 5);
  }
  return { path: shapes.map(toPath).join(""), blocks };
}

export function skyline(seed = 7): Skyline {
  const next = random(seed);
  const far = buildings(next, 110, 230);
  const near = buildings(next, 60, 190);
  const windows: Skyline["windows"] = [];
  const signs: Skyline["signs"] = [];
  for (const { x, right, top } of near.blocks) {
    for (let y = top + 30; y < CITY_HEIGHT - 8; y += 13) {
      for (let wx = x + 7; wx < right - 8; wx += 11) {
        const roll = next();
        if (roll < 0.07) windows.push({ x: wx, y, lit: roll < 0.025 });
      }
    }
    if (top < 200 && next() < 0.18) {
      const y = top + 34;
      const height = Math.min(40 + Math.round(next() * 40), CITY_HEIGHT - y - 8);
      signs.push({ x: right - 12, y, height });
    }
  }
  return { far: far.path, near: near.path, windows, signs };
}
