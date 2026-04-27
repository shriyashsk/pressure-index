import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
const FORMATS = ["ipl", "t20", "odi", "test"];
const GENDERS = ["male", "female"];

export default function Leaderboard() {
  const [role, setRole] = useState("batter");
  const [format, setFormat] = useState("ipl");
  const [gender, setGender] = useState("male");
  const [page, setPage] = useState(1);
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const LIMIT = 20;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const endpoint =
        role === "batter" ? "/players/batters" : "/players/bowlers";
      const res = await axios.get(`${API}${endpoint}`, {
        params: { format, gender, page, limit: LIMIT },
      });
      setData(res.data.results);
      setTotal(res.data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [role, format, gender, page]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);
  useEffect(() => {
    setPage(1);
  }, [role, format, gender]);

  const totalPages = Math.ceil(total / LIMIT);

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <h1 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px" }}>
        Clutch Performance Leaderboard
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "28px" }}>
        Ranked by performance under high-pressure deliveries (Pressure Index ≥
        0.5)
      </p>

      {/* Filters */}
      <div
        style={{
          display: "flex",
          gap: "12px",
          flexWrap: "wrap",
          marginBottom: "24px",
        }}
      >
        {/* Role toggle */}
        <div
          style={{
            display: "flex",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          {["batter", "bowler"].map((r) => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className="btn"
              style={{
                borderRadius: 0,
                background: role === r ? "var(--green)" : "transparent",
                color: role === r ? "#000" : "var(--text-muted)",
              }}
            >
              {r === "batter" ? "🏏 Batters" : "🎯 Bowlers"}
            </button>
          ))}
        </div>

        {/* Format */}
        <div style={{ display: "flex", gap: "6px" }}>
          {FORMATS.map((f) => (
            <button
              key={f}
              onClick={() => setFormat(f)}
              className={`btn ${format === f ? "btn-active" : "btn-outline"}`}
              style={{ textTransform: "uppercase", fontSize: "12px" }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Gender */}
        <div style={{ display: "flex", gap: "6px" }}>
          {GENDERS.map((g) => (
            <button
              key={g}
              onClick={() => setGender(g)}
              className={`btn ${gender === g ? "btn-active" : "btn-outline"}`}
            >
              {g === "male" ? "♂ Male" : "♀ Female"}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr
              style={{
                borderBottom: "1px solid var(--border)",
                background: "rgba(0,0,0,0.2)",
              }}
            >
              {[
                "#",
                "Player",
                "Clutch Score",
                role === "batter"
                  ? "Runs Under Pressure"
                  : "Wickets Under Pressure",
                "HP Balls",
                "Avg Pressure Faced",
              ].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: "14px 20px",
                    textAlign: "left",
                    fontSize: "12px",
                    color: "var(--text-muted)",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.5px",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td
                  colSpan={6}
                  style={{
                    padding: "40px",
                    textAlign: "center",
                    color: "var(--text-muted)",
                  }}
                >
                  Loading...
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  style={{
                    padding: "40px",
                    textAlign: "center",
                    color: "var(--text-muted)",
                  }}
                >
                  No data for this combination
                </td>
              </tr>
            ) : (
              data.map((row, i) => (
                <tr
                  key={i}
                  onClick={() =>
                    navigate(`/player/${encodeURIComponent(row.player)}`)
                  }
                  style={{
                    borderBottom: "1px solid var(--border)",
                    cursor: "pointer",
                    transition: "background 0.15s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.background = "var(--bg-card-hover)")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.background = "transparent")
                  }
                >
                  <td
                    style={{
                      padding: "14px 20px",
                      color: "var(--text-muted)",
                      fontWeight: 600,
                      width: "50px",
                    }}
                  >
                    {(page - 1) * LIMIT + i + 1}
                  </td>
                  <td style={{ padding: "14px 20px", fontWeight: 600 }}>
                    {row.player}
                  </td>
                  <td style={{ padding: "14px 20px" }}>
                    <span
                      className={
                        row.clutch_score > 1 ? "badge-green" : "badge-red"
                      }
                    >
                      {row.clutch_score?.toFixed(3)}
                    </span>
                  </td>
                  <td style={{ padding: "14px 20px" }}>
                    {role === "batter"
                      ? row.runs_under_pressure?.toLocaleString()
                      : row.wickets_under_pressure?.toLocaleString()}
                  </td>
                  <td
                    style={{ padding: "14px 20px", color: "var(--text-muted)" }}
                  >
                    {row.high_pressure_balls?.toLocaleString()}
                  </td>
                  <td
                    style={{ padding: "14px 20px", color: "var(--text-muted)" }}
                  >
                    {(row.avg_pressure_faced * 100)?.toFixed(1)}%
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "20px",
        }}
      >
        <span style={{ color: "var(--text-muted)", fontSize: "14px" }}>
          Showing {(page - 1) * LIMIT + 1}–{Math.min(page * LIMIT, total)} of{" "}
          {total} players
        </span>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className="btn btn-outline"
            onClick={() => setPage((p) => p - 1)}
            disabled={page === 1}
            style={{ opacity: page === 1 ? 0.4 : 1 }}
          >
            ← Prev
          </button>
          <span
            style={{
              padding: "8px 16px",
              color: "var(--text-muted)",
              fontSize: "14px",
            }}
          >
            {page} / {totalPages}
          </span>
          <button
            className="btn btn-outline"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= totalPages}
            style={{ opacity: page >= totalPages ? 0.4 : 1 }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
