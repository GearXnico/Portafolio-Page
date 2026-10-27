import { useEffect, useRef, useState } from "react";
import {
  BoxGeometry,
  type BufferGeometry,
  EdgesGeometry,
  LineBasicMaterial,
  LineSegments,
  PerspectiveCamera,
  Scene,
  SphereGeometry,
  TorusGeometry,
  WebGLRenderer,
  WireframeGeometry,
} from "three";

// Each shape lives a few seconds, then a short glitch swaps it for the next one.
const SHAPE_MS = 4000;
const GLITCH_MS = 360;

const shapes: (() => BufferGeometry)[] = [
  () => new WireframeGeometry(new SphereGeometry(1.3, 12, 9)),
  () => new EdgesGeometry(new BoxGeometry(1.7, 1.7, 1.7)),
  () => new WireframeGeometry(new TorusGeometry(1, 0.38, 10, 28)),
];

/** The hero's neon figure: it rotates, glitches and turns into another shape, as if alive. */
export default function Entity() {
  const host = useRef<HTMLDivElement>(null);
  const [glitching, setGlitching] = useState(false);

  useEffect(() => {
    const element = host.current;
    if (!element) return;

    const renderer = new WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(element.clientWidth, element.clientHeight);
    element.append(renderer.domElement);

    const scene = new Scene();
    const camera = new PerspectiveCamera(45, element.clientWidth / element.clientHeight, 0.1, 20);
    camera.position.z = 4.2;
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
    const material = new LineBasicMaterial({ color: accent, transparent: true, opacity: 0.85 });
    const figure = new LineSegments(shapes[0]?.(), material);
    scene.add(figure);

    let index = 0;
    const pointer = { x: 0, y: 0 };
    const onPointer = (event: PointerEvent) => {
      pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
      pointer.y = (event.clientY / window.innerHeight) * 2 - 1;
    };
    window.addEventListener("pointermove", onPointer);

    let frame = 0;
    let last = performance.now();
    const draw = (now: number) => {
      const seconds = (now - last) / 1000;
      last = now;
      figure.rotation.y += seconds * 0.35;
      // Leans a little towards the pointer.
      figure.rotation.x += (pointer.y * 0.4 - figure.rotation.x) * 0.05;
      figure.rotation.z += (pointer.x * 0.2 - figure.rotation.z) * 0.05;
      renderer.render(scene, camera);
      frame = requestAnimationFrame(draw);
    };
    frame = requestAnimationFrame(draw);

    let swap = 0;
    let settle = 0;
    const cycle = window.setInterval(() => {
      setGlitching(true);
      swap = window.setTimeout(() => {
        index = (index + 1) % shapes.length;
        figure.geometry.dispose();
        figure.geometry = shapes[index]?.() ?? figure.geometry;
      }, GLITCH_MS / 2);
      settle = window.setTimeout(() => {
        setGlitching(false);
      }, GLITCH_MS);
    }, SHAPE_MS);

    return () => {
      cancelAnimationFrame(frame);
      window.clearInterval(cycle);
      window.clearTimeout(swap);
      window.clearTimeout(settle);
      window.removeEventListener("pointermove", onPointer);
      figure.geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return (
    <div ref={host} className={glitching ? "entity glitching" : "entity"} aria-hidden="true" />
  );
}
