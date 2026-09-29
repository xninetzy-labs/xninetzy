import type { EasingName } from "../runtime/types";

export function easingValue(easing: EasingName, t: number, ...args: number[]): number {
  if (t <= 0) return 0;
  if (t >= 1) return 1;
  if (easing === "linear") return t;
  if (easing === "ease_in") return Math.pow(t, 3);
  if (easing === "ease_out") return 1 - Math.pow(1 - t, 3);
  if (easing === "ease_in_out") {
    return t < 0.5
      ? 4 * t * t * t
      : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
  if (easing === "cubic_bezier") {
    if (args.length !== 4) {
      throw new Error("cubic_bezier requires (x1, y1, x2, y2) extra args");
    }
    const [x1, y1, x2, y2] = args;
    let s = t;
    for (let i = 0; i < 8; i += 1) {
      const xs = cb(s, x1, x2);
      const dx = xs - t;
      if (Math.abs(dx) < 1e-6) break;
      const dxs = cbDeriv(s, x1, x2);
      if (dxs === 0) break;
      s -= dx / dxs;
      s = Math.max(0, Math.min(1, s));
    }
    return cb(s, y1, y2);
  }
  if (easing === "spring_deterministic") {
    const decay = Math.exp(-0.6 * 6 * t);
    const osc = Math.cos(8 * t);
    return 1 - decay * osc;
  }
  if (easing === "ease_in_back") {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return c3 * t * t * t - c1 * t * t;
  }
  if (easing === "anticipate") {
    const s = 2;
    return t * t * ((s + 1) * t - s);
  }
  if (easing === "ease_out_back") {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    const u = t - 1;
    return 1 + c3 * u * u * u + c1 * u * u;
  }
  if (easing === "ease_in_out_back") {
    const c2 = 1.70158 * 1.525;
    return t < 0.5
      ? (Math.pow(2 * t, 2) * ((c2 + 1) * 2 * t - c2)) / 2
      : (Math.pow(2 * t - 2, 2) * ((c2 + 1) * (2 * t - 2) + c2) + 2) / 2;
  }
  if (easing === "ease_out_elastic") {
    const c4 = (2 * Math.PI) / 3;
    return Math.pow(2, -10 * t) * Math.sin((10 * t - 0.75) * c4) + 1;
  }
  if (easing === "ease_out_bounce") {
    const n1 = 7.5625;
    const d1 = 2.75;
    let u = t;
    if (u < 1 / d1) return n1 * u * u;
    if (u < 2 / d1) {
      u -= 1.5 / d1;
      return n1 * u * u + 0.75;
    }
    if (u < 2.5 / d1) {
      u -= 2.25 / d1;
      return n1 * u * u + 0.9375;
    }
    u -= 2.625 / d1;
    return n1 * u * u + 0.984375;
  }
  if (easing === "ease_out_expo") {
    return 1 - Math.pow(2, -10 * t);
  }
  if (easing === "ease_out_circ") {
    return Math.sqrt(1 - (t - 1) * (t - 1));
  }
  throw new Error(`unknown easing: ${easing}`);
}

function cb(s: number, a: number, b: number): number {
  const u = 1 - s;
  return 3 * u * u * s * a + 3 * u * s * s * b + s * s * s;
}

function cbDeriv(s: number, a: number, b: number): number {
  const u = 1 - s;
  return 3 * u * u * a - 6 * u * s * a + 6 * u * s * b - 3 * s * s * b + 3 * s * s;
}
