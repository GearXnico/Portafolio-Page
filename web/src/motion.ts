// Whether the hero may load its 3D figure: it is skipped on small screens, when the device asks for
// reduced motion and when the browser has no WebGL.

function matches(query: string): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia(query).matches;
}

function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

export function canShow3D(): boolean {
  return (
    !matches("(prefers-reduced-motion: reduce)") && matches("(min-width: 48rem)") && hasWebGL()
  );
}
