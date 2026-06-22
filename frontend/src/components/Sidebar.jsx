import StatsPanel from './StatsPanel';
import BufferControls from './BufferControls';
import LayerTogglePanel from './LayerTogglePanel';
import ParcelSelector from './ParcelSelector';
import { useAnalysis } from '../hooks/useAnalysis';

const Sidebar = () => {
  const { drawMode, setDrawMode, runAnalysis, selectedParcelId, loading } = useAnalysis();

  return (
    <div className="sidebar-panel">
      <div className="panel-header">
        <h1>Buildable Land</h1>
        <p>Analyze buildable land area and constraints.</p>
      </div>

      <ParcelSelector />

      <div className="draw-mode-section">
        <h3>Draw Mode</h3>
        <div className="mode-toggle-group">
          <button
            className={`mode-btn ${drawMode === 'exclude' ? 'active' : ''}`}
            onClick={() => setDrawMode('exclude')}
          >
            Exclude Area
          </button>
          <button
            className={`mode-btn ${drawMode === 'restore' ? 'active' : ''}`}
            onClick={() => setDrawMode('restore')}
          >
            Restore Area
          </button>
        </div>
        <p className="mode-desc">
          {drawMode === 'exclude'
            ? 'Draw polygons to manually exclude areas from buildable land.'
            : 'Draw polygons to restore previously excluded areas.'}
        </p>
      </div>

      <StatsPanel />
      <BufferControls />
      <LayerTogglePanel />

      <button
        className="action-btn run-btn"
        onClick={() => runAnalysis(selectedParcelId)}
        disabled={loading}
      >
        {loading ? 'Analyzing...' : 'Run Analysis'}
      </button>
    </div>
  );
};

export default Sidebar;
