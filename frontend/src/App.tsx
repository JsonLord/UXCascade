import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AnalysisPage from './pages/AnalysisPage';
import EvaluationPage from './pages/EvaluationPage';
import ExperimentListPage from './pages/ExperimentListPage';
import ExperimentSetupPage from './pages/ExperimentSetupPage';
import FixPage from './pages/FixPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ExperimentListPage />} />
        <Route path="/experiments/new" element={<ExperimentSetupPage />} />
        <Route path="/experiments/:id" element={<AnalysisPage />} />
        <Route
          path="/experiments/:id/journey"
          element={<AnalysisPage initialTab="journey" />}
        />
        <Route
          path="/experiments/:id/issues/:issueId/fix"
          element={<FixPage />}
        />
        <Route
          path="/experiments/:id/issues/:issueId/evaluate"
          element={<EvaluationPage />}
        />
      </Routes>
    </BrowserRouter>
  );
}
