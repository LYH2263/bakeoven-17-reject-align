export function fmtMin(m: number): string {
  const h = Math.floor(m / 60);
  const mm = m % 60;
  return `${String(h).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}

export function fmtInterval(start: number, end: number): string {
  return `${fmtMin(start)}–${fmtMin(end)}`;
}

export function phaseLabel(phase: string | null | undefined): string {
  if (phase === "ferment") return "发酵";
  if (phase === "bake") return "烘烤";
  return phase ?? "";
}

export type Conflict = {
  id: number;
  batch_code: string;
  oven_id: number;
  detail: string;
  created_at: string;
  attempt_phase: string | null;
  attempt_start_min: number | null;
  attempt_end_min: number | null;
  rival_batch_id: number | null;
  rival_code: string | null;
  rival_phase: string | null;
  rival_start_min: number | null;
  rival_end_min: number | null;
};
