import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

type C = {
  id: number;
  batch_code: string;
  oven_id: number;
  detail: string;
  opponent_code?: string | null;
  opponent_phase?: string | null;
  opponent_start_min?: number | null;
  opponent_end_min?: number | null;
  candidate_phase?: string | null;
  candidate_start_min?: number | null;
  candidate_end_min?: number | null;
  created_at: string;
};

const PHASE_CN: Record<string, string> = { ferment: "发酵", bake: "烘烤" };
function fmt(m: number | null | undefined) {
  if (m === null || m === undefined) return "—";
  const h = Math.floor(m / 60), mm = m % 60;
  return `${String(h).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
}
function range(s: number | null | undefined, e: number | null | undefined) {
  if (s === null || s === undefined || e === null || e === undefined) return "—";
  return `${fmt(s)}–${fmt(e)}`;
}
function phase(ph: string | null | undefined) {
  return ph ? PHASE_CN[ph] ?? ph : "—";
}

export default function ConflictsPage() {
  const [rows, setRows] = useState<C[]>([]);
  useEffect(() => { api<C[]>("/conflicts").then(setRows); }, []);
  return (<>
    <h2>冲突</h2>
    <table className="table">
      <thead><tr>
        <th>时间</th><th>拟排批次</th><th>炉位</th>
        <th>对手批次</th><th>对手阶段</th><th>对手色块起止</th>
        <th>拟排阶段</th><th>拟排起止</th>
      </tr></thead>
      <tbody>{rows.map(c => <tr key={c.id}>
        <td className="mono">{new Date(c.created_at).toLocaleString()}</td>
        <td>{c.batch_code}</td>
        <td>#{c.oven_id}</td>
        <td>{c.opponent_code
          ? <Link to={`/batches?code=${encodeURIComponent(c.opponent_code)}`}>{c.opponent_code}</Link>
          : "—"}</td>
        <td>{phase(c.opponent_phase)}</td>
        <td className="mono">{range(c.opponent_start_min, c.opponent_end_min)}</td>
        <td>{phase(c.candidate_phase)}</td>
        <td className="mono">{range(c.candidate_start_min, c.candidate_end_min)}</td>
      </tr>)}</tbody>
    </table>
  </>);
}
