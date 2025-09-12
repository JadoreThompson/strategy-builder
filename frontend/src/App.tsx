import { BrowserRouter, Route, Routes } from "react-router";
import AccountsPage from "./pages/AccountsPage";
import CreateStrategyPage from "./pages/CreateStrategyPage";
import CreateVersionPage from "./pages/CreateVersionPage";
import StrategiesPage from "./pages/StrategiesPage";
import StrategyVersionPage from "./pages/StrategyVersionPage";
import StrategyVersionsPage from "./pages/StrategyVersionsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/create-strategy" element={<CreateStrategyPage />} />
        <Route path="/create-version" element={<CreateVersionPage />} />
        <Route path="/strategies" element={<StrategiesPage />} />
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
