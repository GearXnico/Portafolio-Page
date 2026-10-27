import { act, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Entity from "../src/components/Entity";

// jsdom has no WebGL, so three.js is replaced by stand-ins that record what the figure does.
const three = vi.hoisted(() => {
  const disposed: string[] = [];
  const state = { failRenderer: false };

  class Disposable {
    constructor(private readonly name: string) {}
    dispose() {
      disposed.push(this.name);
    }
  }
  class Geometry extends Disposable {
    constructor() {
      super("geometry");
    }
  }
  class WebGLRenderer extends Disposable {
    domElement = document.createElement("canvas");
    constructor() {
      super("renderer");
      if (state.failRenderer) throw new Error("no context");
    }
    setPixelRatio() {}
    setSize() {}
    render() {}
  }
  class LineBasicMaterial extends Disposable {
    constructor() {
      super("material");
    }
  }
  class LineSegments {
    rotation = { x: 0, y: 0, z: 0 };
    constructor(public geometry: Geometry) {}
  }

  return {
    disposed,
    state,
    module: {
      BoxGeometry: Geometry,
      EdgesGeometry: Geometry,
      SphereGeometry: Geometry,
      TorusGeometry: Geometry,
      WireframeGeometry: Geometry,
      LineBasicMaterial,
      LineSegments,
      WebGLRenderer,
      PerspectiveCamera: class {
        position = { z: 0 };
      },
      Scene: class {
        add() {}
      },
    },
  };
});

vi.mock("three", () => three.module);

afterEach(() => {
  three.disposed.length = 0;
  three.state.failRenderer = false;
  vi.useRealTimers();
});

describe("Entity", () => {
  it("draws on a canvas and releases everything when it leaves the page", () => {
    const { container, unmount } = render(<Entity />);

    expect(container.querySelector(".entity canvas")).toBeInTheDocument();
    unmount();

    expect(three.disposed).toEqual(expect.arrayContaining(["geometry", "material", "renderer"]));
  });

  it("glitches and swaps to the next shape every few seconds", () => {
    vi.useFakeTimers();
    const { container } = render(<Entity />);

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(container.querySelector(".entity")).toHaveClass("glitching");

    act(() => {
      vi.advanceTimersByTime(360);
    });
    expect(three.disposed).toContain("geometry");
    expect(container.querySelector(".entity")).not.toHaveClass("glitching");
  });

  it("if WebGL fails, stays empty instead of breaking the page", () => {
    three.state.failRenderer = true;

    const { container } = render(<Entity />);

    expect(container.querySelector(".entity")).toBeEmptyDOMElement();
  });
});
