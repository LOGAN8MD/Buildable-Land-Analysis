import Home from './pages/Home';
import { AnalysisProvider } from './context/AnalysisContext.jsx';

function App() {
  return (
    <AnalysisProvider>
      <div className="app-container">
        <Home />
      </div>
    </AnalysisProvider>
  );
}

export default App;
