import { Link, useLocation } from "react-router-dom";

export default function Navbar() {
  const { pathname } = useLocation();

  const links = [
    { to: "/", label: "🏆 Leaderboard" },
    { to: "/matches", label: "📈 Match Timeline" },
  ];

  return (
    <nav
      style={{
        background: "var(--bg-card)",
        borderBottom: "1px solid var(--border)",
        padding: "0 32px",
        display: "flex",
        alignItems: "center",
        gap: "32px",
        height: "60px",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <span
        style={{
          fontWeight: 700,
          fontSize: "18px",
          color: "var(--green)",
          letterSpacing: "0.5px",
        }}
      >
        🏏 Pressure Index
      </span>

      <div style={{ display: "flex", gap: "8px" }}>
        {links.map(({ to, label }) => (
          <Link
            key={to}
            to={to}
            style={{
              padding: "6px 16px",
              borderRadius: "8px",
              fontSize: "14px",
              fontWeight: 500,
              color: pathname === to ? "var(--green)" : "var(--text-muted)",
              background:
                pathname === to ? "rgba(0,200,83,0.1)" : "transparent",
              transition: "all 0.2s",
            }}
          >
            {label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
