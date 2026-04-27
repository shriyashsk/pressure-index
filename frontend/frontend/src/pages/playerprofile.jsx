import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
);

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function PlayerProfile() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get(`${API}/players/${encodeURIComponent(name)}/profile`)
      .then((r) => setData(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [name]);

  if (loading)
    return (
      <div
        style={{
          padding: "80px",
          textAlign: "center",
          color: "var(--text-muted)",
        }}
      >
        Loading player profile...
      </div>
    );

  if (!data || data.error)
    return (
      <div
        style={{ padding: "80px", textAlign: "center", color: "var(--red)" }}
      >
        Player not found.
      </div>
    );

  const batterRows = data.by_format?.filter((r) => r.role === "batter") || [];
  const bowlerRows = data.by_format?.filter((r) => r.role === "bowler") || [];

  const chartData = {
    labels: batterRows.map((r) => r.format?.toUpperCase()),
    datasets: [
      {
        label: "Clutch Score by Format",
        data: batterRows.map((r) => r.clutch_score),
        backgroundColor: batterRows.map((r) =>
          r.clutch_score > 1
            ? "rgba(0, 200, 83, 0.7)"
            : "rgba(255, 61, 87, 0.7)",
        ),
        borderColor: batterRows.map((r) =>
          r.clutch_score > 1 ? "#00c853" : "#ff3d57",
        ),
        borderWidth: 1,
        borderRadius: 6,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => ` Clutch Score: ${ctx.parsed.y.toFixed(3)}`,
        },
      },
    },
    scales: {
      x: { ticks: { color: "#64748b" }, grid: { color: "#2d3149" } },
      y: { ticks: { color: "#64748b" }, grid: { color: "#2d3149" } },
    },
  };

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "32px 24px" }}>
      {/* Back */}
      <button
        className="btn btn-outline"
        onClick={() => navigate(-1)}
        style={{ marginBottom: "24px" }}
      >
        ← Back
      </button>

      {/* Header */}
      <div className="card" style={{ marginBottom: "24px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <h1
              style={{ fontSize: "32px", fontWeight: 700, marginBottom: "8px" }}
            >
              {data.player}
            </h1>
            <span style={{ color: "var(--text-muted)", fontSize: "14px" }}>
              Cricket Pressure Profile
            </span>
          </div>
          <div style={{ textAlign: "center" }}>
            <div
              style={{
                fontSize: "48px",
                fontWeight: 800,
                color:
                  data.overall_clutch_score > 1 ? "var(--green)" : "var(--red)",
              }}
            >
              {data.overall_clutch_score?.toFixed(3)}
            </div>
            <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>
              Overall Clutch Score
            </div>
          </div>
        </div>
      </div>

      {/* Chart */}
      {batterRows.length > 0 && (
        <div className="card" style={{ marginBottom: "24px" }}>
          <h2
            style={{ fontSize: "18px", fontWeight: 600, marginBottom: "20px" }}
          >
            Clutch Score by Format
          </h2>
          <Bar data={chartData} options={chartOptions} height={80} />
        </div>
      )}

      {/* Batter stats table */}
      {batterRows.length > 0 && (
        <div className="card" style={{ marginBottom: "24px" }}>
          <h2
            style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}
          >
            🏏 Batting Under Pressure
          </h2>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {[
                  "Format",
                  "Gender",
                  "Clutch Score",
                  "Runs",
                  "HP Balls",
                  "Avg Pressure",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {batterRows.map((r, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      style={{
                        textTransform: "uppercase",
                        fontWeight: 600,
                        color: "var(--green)",
                        fontSize: "12px",
                      }}
                    >
                      {r.format}
                    </span>
                  </td>
                  <td
                    style={{ padding: "12px 16px", color: "var(--text-muted)" }}
                  >
                    {r.gender}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      className={
                        r.clutch_score > 1 ? "badge-green" : "badge-red"
                      }
                    >
                      {r.clutch_score?.toFixed(3)}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    {r.runs_under_pressure?.toLocaleString()}
                  </td>
                  <td
                    style={{ padding: "12px 16px", color: "var(--text-muted)" }}
                  >
                    {r.high_pressure_balls?.toLocaleString()}
                  </td>
                  <td
                    style={{ padding: "12px 16px", color: "var(--text-muted)" }}
                  >
                    {(r.avg_pressure_faced * 100)?.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Bowler stats table */}
      {bowlerRows.length > 0 && (
        <div className="card">
          <h2
            style={{ fontSize: "18px", fontWeight: 600, marginBottom: "16px" }}
          >
            🎯 Bowling Under Pressure
          </h2>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                {[
                  "Format",
                  "Gender",
                  "Clutch Score",
                  "Wickets",
                  "HP Balls",
                ].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "10px 16px",
                      textAlign: "left",
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      fontWeight: 600,
                      textTransform: "uppercase",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {bowlerRows.map((r, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      style={{
                        textTransform: "uppercase",
                        fontWeight: 600,
                        color: "var(--green)",
                        fontSize: "12px",
                      }}
                    >
                      {r.format}
                    </span>
                  </td>
                  <td
                    style={{ padding: "12px 16px", color: "var(--text-muted)" }}
                  >
                    {r.gender}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      className={
                        r.clutch_score > 5 ? "badge-green" : "badge-red"
                      }
                    >
                      {r.clutch_score?.toFixed(3)}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    {r.wickets_under_pressure?.toLocaleString()}
                  </td>
                  <td
                    style={{ padding: "12px 16px", color: "var(--text-muted)" }}
                  >
                    {r.high_pressure_balls?.toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
