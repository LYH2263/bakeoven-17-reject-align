import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { Conflict, fmtInterval, phaseLabel } from "../utils/schedule";

const DASH = "—";

export default function ConflictsPage() {
  const [rows, setRows] = useState<Conflict[]>([]);
  useEffect(() => { api<Conflict[]>("/conflicts").then(setRows); }, []);
  return (<>
    <h2>冲突</h2>
    <table className="table"><thead><tr>
      <th>时间</th><th>本次批次</th><th>炉位</th><th>本次阶段</th><th>本次区间</th>
      <th>对手批次</th><th>对手阶段</th><th>对手区间</th><th>详情</th>
    </tr></thead>
    <tbody>{rows.map(c => <tr key={c.id}>
      <td className="mono">{new Date(c.created_at).toLocaleString()}</td>
      <td className="mono">{c.batch_code}</td>
      <td>{c.oven_id}</td>
      <td>{c.attempt_phase ? phaseLabel(c.attempt_phase) : DASH}</td>
      <td className="mono">{c.attempt_start_min != null && c.attempt_end_min != null
        ? fmtInterval(c.attempt_start_min, c.attempt_end_min) : DASH}</td>
      <td className="mono">{c.rival_code
        ? <Link className="batch-link" to={`/batches?code=${encodeURIComponent(c.rival_code)}`}>{c.rival_code}</Link>
        : DASH}</td>
      <td>{c.rival_phase ? phaseLabel(c.rival_phase) : DASH}</td>
      <td className="mono">{c.rival_start_min != null && c.rival_end_min != null
        ? fmtInterval(c.rival_start_min, c.rival_end_min) : DASH}</td>
      <td className="conflict-detail-cell">{c.detail}</td>
    </tr>)}</tbody></table>
  </>);
}
