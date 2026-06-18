import { BrowserRouter, Routes, Route } from "react-router-dom";

import "./App.css";

import Home from "./pages/Home";
import ResearchDashboard from "./pages/ResearchDashboard";
import PublicDashboard from "./pages/PublicDashboard";
import DrugSearch from "./pages/DrugSearch";

import Navbar from "./components/Navbar";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/research" element={<ResearchDashboard />} />
        <Route path="/user" element={<PublicDashboard />} />
        <Route path="/search" element={<DrugSearch />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;