import { useState, useEffect } from "react";
import axios from "axios";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function MatchTimeline() {
  const [matchId, setMatchId] = useState("");
  const [innings, setInnings] = useState(1);
  const [data, setData] = useState(null);
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [format, setFormat] = useState("ipl");

  const FORMATS = ["ipl", "t20", "odi", "test"];

  useEffect(() => {
    axios
      .get(`${API}/matches/`, { params: { format, limit: 50 } })
      .then((r) => {
        setMatches(r.data.results);
        setMatchId("");
        setData(null);
      })
      .catch(console.error);
  }, [format]);

  const fetchTimeline = async () => {
    if (!matchId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/matches/${matchId}/timeline`, {
        params: { innings },
      });
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data
    ? {
        labels: data.timeline.map((d, i) => `${d.over}.${d.ball}`),
        datasets: [
          {
            label: "Pressure Index",
            data: data.timeline.map((d) => d.pressure_index),
            borderColor: "#ff3d57",
            backgroundColor: "rgba(255, 61, 87, 0.1)",
            fill: true,
            tension: 0.3,
            pointRadius: data.timeline.map((d) => (d.is_wicket ? 6 : 2)),
            pointBackgroundColor: data.timeline.map((d) =>
              d.is_wicket ? "#ff3d57" : "rgba(255,61,87,0.5)",
            ),
            pointBorderColor: data.timeline.map((d) =>
              d.is_wicket ? "#fff" : "transparent",
            ),
            pointBorderWidth: data.timeline.map((d) => (d.is_wicket ? 2 : 0)),
          },
          {
            label: "CRR",
            data: data.timeline.map((d) =>
              d.crr ? Math.min(d.crr, 20) : null,
            ),
            borderColor: "#00c853",
            backgroundColor: "transparent",
            tension: 0.3,
            pointRadius: 0,
            borderWidth: 1.5,
            borderDash: [4, 4],
          },
        ],
      }
    : null;

  const chartOptions = {
    responsive: true,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        labels: { color: "#e2e8f0", font: { size: 12 } },
      },
      tooltip: {
        callbacks: {
          afterBody: (items) => {
            const idx = items[0]?.dataIndex;
            if (idx === undefined || !data) return "";
            const d = data.timeline[idx];
            const lines = [
              `Batter: ${d.batter}`,
              `Bowler: ${d.bowler}`,
              `Runs: ${d.runs_scored}`,
            ];
            if (d.is_wicket) lines.push(`🔴 WICKET: ${d.wicket_kind}`);
            return lines;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#64748b", maxTicksLimit: 20 },
        grid: { color: "#2d3149" },
      },
      y: {
        min: 0,
        max: 1,
        ticks: { color: "#64748b" },
        grid: { color: "#2d3149" },
      },
    },
  };

  return (
    <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "32px 24px" }}>
      <h1 style={{ fontSize: "28px", fontWeight: 700, marginBottom: "8px" }}>
        Match Pressure Timeline
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: "28px" }}>
        Pressure Index across every delivery of an innings. Red dots = wickets.
      </p>

      {/* Controls */}
      <div className="card" style={{ marginBottom: "24px" }}>
        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            alignItems: "flex-end",
          }}
        >
          {/* Format */}
          <div>
            <label
              style={{
                fontSize: "12px",
                color: "var(--text-muted)",
                display: "block",
                marginBottom: "6px",
              }}
            >
              FORMAT
            </label>
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
          </div>

          {/* Match selector */}
          <div style={{ flex: 1, minWidth: "200px" }}>
            <label
              style={{
                fontSize: "12px",
                color: "var(--text-muted)",
                display: "block",
                marginBottom: "6px",
              }}
            >
              MATCH
            </label>
            <select
              value={matchId}
              onChange={(e) => setMatchId(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                background: "var(--bg-primary)",
                color: "var(--text)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                fontSize: "14px",
              }}
            >
              <option value="">Select a match...</option>
              {matches.map((m) => (
                <option key={m.match_id} value={m.match_id}>
                  {m.team_batting} vs {m.team_bowling} — {m.match_date}
                </option>
              ))}
            </select>
          </div>

          {/* Innings */}
          <div>
            <label
              style={{
                fontSize: "12px",
                color: "var(--text-muted)",
                display: "block",
                marginBottom: "6px",
              }}
            >
              INNINGS
            </label>
            <div style={{ display: "flex", gap: "6px" }}>
              {[1, 2].map((n) => (
                <button
                  key={n}
                  onClick={() => setInnings(n)}
                  className={`btn ${innings === n ? "btn-active" : "btn-outline"}`}
                >
                  {n === 1 ? "1st" : "2nd"}
                </button>
              ))}
            </div>
          </div>

          <button
            className="btn btn-green"
            onClick={fetchTimeline}
            disabled={!matchId || loading}
          >
            {loading ? "Loading..." : "View Timeline"}
          </button>
        </div>
      </div>

      {/* Chart */}
      {data && chartData && (
        <>
          <div className="card" style={{ marginBottom: "24px" }}>
            <h2
              style={{
                fontSize: "16px",
                fontWeight: 600,
                marginBottom: "20px",
              }}
            >
              Pressure Curve — Innings {innings}
              <span
                style={{
                  color: "var(--text-muted)",
                  fontWeight: 400,
                  fontSize: "14px",
                  marginLeft: "12px",
                }}
              >
                {data.total_balls} balls
              </span>
            </h2>
            <Line data={chartData} options={chartOptions} />
          </div>

          {/* Peak pressure moments */}
          <div className="card">
            <h2
              style={{
                fontSize: "16px",
                fontWeight: 600,
                marginBottom: "16px",
              }}
            >
              🔥 Peak Pressure Moments
            </h2>
            <div
              style={{ display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {data.peak_pressure_moments.map((m, i) => (
                <div
                  key={i}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 16px",
                    background: "var(--bg-primary)",
                    borderRadius: "8px",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <span style={{ fontWeight: 600 }}>
                      Over {m.over}.{m.ball}
                    </span>
                    <span
                      style={{
                        color: "var(--text-muted)",
                        fontSize: "13px",
                        marginLeft: "12px",
                      }}
                    >
                      {m.batter} vs {m.bowler}
                    </span>
                    {m.is_wicket === 1 && (
                      <span className="badge-red" style={{ marginLeft: "8px" }}>
                        WICKET
                      </span>
                    )}
                  </div>
                  <span
                    style={{
                      fontWeight: 700,
                      fontSize: "16px",
                      color:
                        m.pressure_index > 0.7 ? "var(--red)" : "var(--text)",
                    }}
                  >
                    {(m.pressure_index * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
