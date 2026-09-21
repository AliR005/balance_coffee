import { Route, Routes } from "react-router-dom";
import { HealthPage } from "./pages/HealthPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<HealthPage />} />
    </Routes>
  );
}
