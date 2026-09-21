import { Route, Routes } from "react-router-dom";
import { UiShowcase } from "../dev/UiShowcase";
import { HealthPage } from "./pages/HealthPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<HealthPage />} />
      {import.meta.env.DEV ? <Route path="/dev/ui" element={<UiShowcase />} /> : null}
    </Routes>
  );
}
