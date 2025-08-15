import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import Navbar from "./components/layout/Navbar";
import Home from "./pages/Home";
import Browse from "./pages/Browse";
import Drink from "./pages/Drink";
import Profile from "./pages/Profile";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import NotFound from "./pages/NotFound";
import { getUserId } from "./lib/storage";

export default function App() {
  const loc = useLocation();
  const [authed, setAuthed] = useState<boolean>(!!getUserId());

  // Re-read auth on every navigation (and after login sets localStorage)
  useEffect(() => {
    setAuthed(!!getUserId());
  }, [loc.key]);

  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/login" element={authed ? <Navigate to="/onboarding" /> : <Login />} />
        <Route path="/onboarding" element={authed ? <Onboarding /> : <Navigate to="/login" />} />
        <Route path="/" element={authed ? <Home /> : <Navigate to="/login" />} />
        <Route path="/browse" element={<Browse />} />
        <Route path="/drink/:id" element={<Drink />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}
