import { BrowserRouter, Route, Routes } from "react-router";
import CreateStrategyPage from "./pages/CreateStrategyPage";
import CreateVersionPage from "./pages/CreateVersionPage";
import PositionsPage from "./pages/PositionsPage";
import StrategiesPage from "./pages/StrategiesPage";
import StrategyVersionPage from "./pages/StrategyVersionPage";
import StrategyVersionsPage from "./pages/StrategyVersionsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/positions" element={<PositionsPage />} />
        <Route path="/strategies" element={<StrategiesPage />} />
        <Route path="/create-strategy" element={<CreateStrategyPage />} />
        <Route path="/create-version" element={<CreateVersionPage />} />
        <Route
          path="/strategies/:strategyId"
          element={<StrategyVersionsPage />}
        />
        <Route
          path="/strategies/versions/:versionId"
          element={<StrategyVersionPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
