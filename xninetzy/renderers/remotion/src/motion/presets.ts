import type { EasingName, Keyframe } from "../runtime/types";

export type PresetSpec = {
  primitive: string;
  target: string;
  start_frame: number;
  end_frame: number;
  easing: EasingName;
  parameters?: Record<string, number>;
};

export const CANONICAL_PRIMITIVES: ReadonlySet<string> = new Set<string>([
  "FadeIn", "FadeOut", "SlideIn", "SlideOut",
  "ScaleIn", "ScaleOut", "Zoom", "Pan", "Reveal",
  "Typewriter", "BlurIn", "BlurOut", "Pop",
  "Spring", "Stagger", "Highlight", "Spotlight",
  "CameraPush", "CameraPull", "KenBurns",
  "LowerThird", "TitleCard", "Callout", "CodeHighlight",
  "BrowserFrame", "DeviceFrame",
  "Bounce", "Elastic", "Rotate", "Flip3D", "Swing",
  "Wiggle", "Shake", "Orbit", "Parallax", "PathMove",
  "MotionBlurStreak", "GlowPulse", "PulseScale",
]);

export function isCanonical(primitive: string): boolean {
  return CANONICAL_PRIMITIVES.has(primitive);
}

export function primitiveToKeyframes(spec: PresetSpec): Keyframe[] {
  const { primitive, start_frame: start, end_frame: end, easing, parameters = {} } = spec;
  const span = end - start;
  if (span <= 0) {
    throw new Error("invalid motion preset frame window");
  }

  switch (primitive) {
    case "FadeIn":
      return ease("opacity", start, end, 0, 1, easing, { "0": 0 });
    case "FadeOut":
      return ease("opacity", start, end, 1, 0, easing);
    case "SlideIn": {
      const x0 = parameters["direction"] === "right" ? 1 : -1;
      return ease("x", start, end, x0, 0, easing, { [String(start)]: x0 });
    }
    case "SlideOut": {
      const x1 = parameters["direction"] === "left" ? -1 : 1;
      return ease("x", start, end, 0, x1, easing);
    }
    case "ScaleIn":
      return ease("scale", start, end, parameters["from_scale"] ?? 0.8, 1, easing);
    case "ScaleOut":
      return ease("scale", start, end, 1, parameters["to_scale"] ?? 1.2, easing);
    case "Zoom":
      return ease("scale", start, end, 1, parameters["to_scale"] ?? 1.12, easing);
    case "Pan":
      return ease(
        "x",
        start,
        end,
        parameters["from_x"] ?? 0,
        parameters["to_x"] ?? 0,
        easing
      );
    case "Reveal":
      return ease("clip_path", start, end, 0, parameters["to_clip"] ?? 1, easing);
    case "CameraPush":
      return ease("scale", start, end, 1, parameters["to_scale"] ?? 1.06, easing);
    case "CameraPull":
      return ease("scale", start, end, 1, parameters["to_scale"] ?? 0.96, easing);
    case "LowerThird":
      return ease("lowerthird_opacity", start, end, 0, 1, easing);
    case "TitleCard":
      return ease("titlecard_opacity", start, end, 0, 1, easing);
    case "BrowserFrame":
      return [{ property: "browser_chrome", frame: start, value: 1, easing }];
    case "DeviceFrame":
      return [{ property: "device_chrome", frame: start, value: 1, easing }];
    case "Bounce":
      return ease("y", start, end, parameters["from_y"] ?? -1, parameters["to_y"] ?? 0, "ease_out_bounce");
    case "Elastic":
      return ease("scale", start, end, parameters["from_scale"] ?? 0.6, parameters["to_scale"] ?? 1, "ease_out_elastic");
    case "Rotate":
      return ease("rotate", start, end, parameters["from_deg"] ?? 0, parameters["to_deg"] ?? 360, easing);
    case "Flip3D":
      return ease("rotate_y", start, end, parameters["from_deg"] ?? 0, parameters["to_deg"] ?? 180, easing);
    case "Parallax":
      return ease("x", start, end, parameters["from_x"] ?? 0, (parameters["to_x"] ?? -0.2) * (parameters["depth"] ?? 1), easing);
    case "PathMove":
      return [
        ...ease("x", start, end, parameters["from_x"] ?? 0, parameters["to_x"] ?? 0, easing),
        ...ease("y", start, end, parameters["from_y"] ?? 0, parameters["to_y"] ?? 0, easing),
      ];
    case "MotionBlurStreak": {
      const mid = start + Math.max(1, Math.floor(span / 2));
      return [
        { property: "motion_blur", frame: start, value: 0, easing },
        { property: "motion_blur", frame: mid, value: parameters["amount"] ?? 1, easing },
        { property: "motion_blur", frame: end, value: 0, easing },
      ];
    }
    case "Swing": {
      const amp = parameters["amplitude_deg"] ?? 18;
      const decay = parameters["decay"] ?? 3;
      const freq = parameters["frequency"] ?? 1.5;
      return sampled("rotate", start, end, (t) => amp * Math.exp(-decay * t) * Math.cos(2 * Math.PI * freq * t), parameters["samples"] ?? 16);
    }
    case "Wiggle": {
      const amp = parameters["amplitude_deg"] ?? 8;
      const cycles = parameters["cycles"] ?? 3;
      return sampled("rotate", start, end, (t) => amp * Math.sin(2 * Math.PI * cycles * t), parameters["samples"] ?? 16);
    }
    case "Shake": {
      const amp = parameters["amplitude"] ?? 0.03;
      const decay = parameters["decay"] ?? 4;
      const freq = parameters["frequency"] ?? 6;
      return sampled("x", start, end, (t) => amp * Math.exp(-decay * t) * Math.sin(2 * Math.PI * freq * t), parameters["samples"] ?? 20);
    }
    case "Orbit": {
      const radius = parameters["radius"] ?? 0.1;
      const phase = parameters["phase"] ?? 0;
      const turns = parameters["turns"] ?? 1;
      const samples = parameters["samples"] ?? 16;
      const baseX = radius * Math.cos(phase);
      const baseY = radius * Math.sin(phase);
      return [
        ...sampled("x", start, end, (t) => radius * Math.cos(2 * Math.PI * turns * t + phase) - baseX, samples),
        ...sampled("y", start, end, (t) => radius * Math.sin(2 * Math.PI * turns * t + phase) - baseY, samples),
      ];
    }
    case "GlowPulse": {
      const count = parameters["count"] ?? 2;
      return sampled("glow", start, end, (t) => 0.5 * (1 - Math.cos(2 * Math.PI * count * t)), parameters["samples"] ?? 16);
    }
    case "PulseScale": {
      const amp = parameters["amplitude"] ?? 0.08;
      const count = parameters["count"] ?? 1;
      return sampled("scale", start, end, (t) => 1 + amp * Math.sin(Math.PI * count * t), parameters["samples"] ?? 14);
    }
    default:
      throw new Error(`primitive '${primitive}' not implemented`);
  }
}

function sampled(
  property: string,
  start: number,
  end: number,
  fn: (t: number) => number,
  samples: number
): Keyframe[] {
  const span = end - start;
  if (span <= 0) {
    throw new Error("invalid sampling window");
  }
  const count = Math.max(2, Math.min(Math.floor(samples), span + 1));
  const keys: Keyframe[] = [];
  let lastFrame = -1;
  for (let i = 0; i < count; i += 1) {
    const t = i / (count - 1);
    let frame = start + Math.round(span * t);
    if (frame <= lastFrame) frame = lastFrame + 1;
    if (frame > end) break;
    keys.push({ property, frame, value: fn(t), easing: "linear" });
    lastFrame = frame;
  }
  if (keys.length === 0 || keys[keys.length - 1]!.frame !== end) {
    keys.push({ property, frame: end, value: fn(1), easing: "linear" });
  }
  return keys;
}

function ease(
  property: string,
  start: number,
  end: number,
  fromValue: number,
  toValue: number,
  easing: EasingName,
  anchors: Record<string, number> = {}
): Keyframe[] {
  const steps = 4;
  const keys: Keyframe[] = [];
  if (anchors[String(start)] !== undefined) {
    keys.push({ property, frame: start, value: anchors[String(start)]!, easing });
  } else {
    keys.push({ property, frame: start, value: fromValue, easing });
  }
  for (let i = 1; i < steps; i += 1) {
    const t = i / steps;
    const frame = start + Math.round((end - start) * t);
    keys.push({ property, frame, value: fromValue, easing });
  }
  keys.push({ property, frame: end, value: toValue, easing });
  return keys;
}
