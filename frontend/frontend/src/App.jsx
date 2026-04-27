import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/navbar";
import Leaderboard from "./pages/leaderboard";
import PlayerProfile from "./pages/playerprofile";
import MatchTimeline from "./pages/matchtimeline";

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Leaderboard />} />
        <Route path="/player/:name" element={<PlayerProfile />} />
        <Route path="/matches" element={<MatchTimeline />} />
      </Routes>
    </BrowserRouter>
  );
}
