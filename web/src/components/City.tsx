import { CITY_HEIGHT, skyline } from "../city";

const city = skyline();

/** Decorative skyline at the bottom of the hero. */
export function City() {
  return (
    <svg
      className="city"
      aria-hidden="true"
      viewBox={["0 0 1440", CITY_HEIGHT].join(" ")}
      preserveAspectRatio="xMidYMax slice"
    >
      <path className="city-far" d={city.far} />
      <path className="city-near" d={city.near} />
      {city.windows.map(({ x, y, lit }) => (
        <rect
          key={`${String(x)}-${String(y)}`}
          className={lit ? "lit" : "window"}
          x={x}
          y={y}
          width={4}
          height={6}
        />
      ))}
      {city.signs.map(({ x, y, height }) => (
        <rect key={`sign-${String(x)}`} className="sign" x={x} y={y} width={5} height={height} />
      ))}
    </svg>
  );
}
