export type EasingName =
  | "linear"
  | "ease_in"
  | "ease_out"
  | "ease_in_out"
  | "cubic_bezier"
  | "spring_deterministic"
  | "ease_in_back"
  | "ease_out_back"
  | "ease_in_out_back"
  | "ease_out_elastic"
  | "ease_out_bounce"
  | "ease_out_expo"
  | "ease_out_circ"
  | "anticipate";

export type Keyframe = {
  property: string;
  frame: number;
  value: number;
  easing: EasingName;
};

export type RenderSettings = {
  width: number;
  height: number;
  fps: number;
  duration_frames: number;
  quality: string;
  format: string;
};

export type CompositionData = {
  composition_id: string;
  name: string;
  resolution: { width: number; height: number };
  fps: number;
  duration_frames: number;
  background_color: string;
  preset: string;
};

export type TrackData = {
  track_id: string;
  composition_id: string;
  kind: string;
  name: string;
  z_index: number;
  clips: Array<Record<string, unknown>>;
};

export type TransitionData = {
  transition_id: string;
  kind: string;
  duration_frames: number;
};

export type SceneData = {
  scene_id: string;
  composition_id: string;
  name: string;
  purpose: string;
  start_frame: number;
  duration_frames: number;
  tracks: TrackData[];
  transition_in: TransitionData | null;
  transition_out: TransitionData | null;
};

export type AssetData = {
  asset_id: string;
  kind: string;
  source_path: string;
  mime_type: string;
  content_hash: string;
  width?: number | null;
  height?: number | null;
  duration_seconds?: number | null;
  fps?: number | null;
};

export type ProjectData = {
  schema_version: string;
  render: RenderSettings;
  project_id: string;
  project_name: string;
  composition: CompositionData | null;
  scenes: SceneData[];
  assets: AssetData[];
};

export type RuntimeProps = {
  schema_version?: string;
  render?: Partial<RenderSettings>;
  project_id?: string;
  project_name?: string;
  composition?: CompositionData | null;
  scenes?: SceneData[];
  assets?: AssetData[];
};
