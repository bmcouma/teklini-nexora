import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { NewIncident } from "./pages/NewIncident";
import { InvestigationView } from "./pages/InvestigationView";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewIncident />} />
          <Route path="/incidents/:incidentId" element={<InvestigationView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
