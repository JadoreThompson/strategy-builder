import { BrowserRouter, Route, Routes } from "react-router";
import PositionsPage from "./pages/PositionsPage";
import StrategiesPage from "./pages/StrategiesPage";
import StrategyVersionsPage from "./pages/StrategyVersionsPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/positions" element={<PositionsPage />} />
        <Route path="/strategies" element={<StrategiesPage />} />
        <Route
          path="/strategies/:strategyId"
          element={<StrategyVersionsPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
