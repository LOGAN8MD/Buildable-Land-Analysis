import { useEffect } from 'react';
import { useAnalysis } from '../hooks/useAnalysis';

const BufferControls = () => {
  const { buffers, updateBuffers, fetchConfig, saveConfig, loading } = useAnalysis();
  // Fetch initial config on mount
  useEffect(() => {
    fetchConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numValue = Number(value);
    updateBuffers({ [name]: numValue });
  };

  const handleRelease = () => {
    saveConfig(buffers);
  };

  return (
    <div className="buffer-controls-section">
      <h3>Buffer Settings (ft)</h3>
      <div className="buffer-controls-list">
        
        <div className="buffer-control-item">
          <div className="buffer-label">
            <span>Wetlands</span>
            <span>{buffers.wetlands} ft</span>
          </div>
          <input
            type="range"
            name="wetlands"
            min="0"
            max="500"
            step="10"
            value={buffers.wetlands}
            onChange={handleChange}
            onMouseUp={handleRelease}
            onTouchEnd={handleRelease}
            disabled={loading}
          />
        </div>

        <div className="buffer-control-item">
          <div className="buffer-label">
            <span>Flood Zones</span>
            <span>{buffers.floodzones} ft</span>
          </div>
          <input
            type="range"
            name="floodzones"
            min="0"
            max="500"
            step="10"
            value={buffers.floodzones}
            onChange={handleChange}
            onMouseUp={handleRelease}
            onTouchEnd={handleRelease}
            disabled={loading}
          />
        </div>

        <div className="buffer-control-item">
          <div className="buffer-label">
            <span>Buildings</span>
            <span>{buffers.buildings} ft</span>
          </div>
          <input
            type="range"
            name="buildings"
            min="0"
            max="500"
            step="10"
            value={buffers.buildings}
            onChange={handleChange}
            onMouseUp={handleRelease}
            onTouchEnd={handleRelease}
            disabled={loading}
          />
        </div>

      </div>
    </div>
  );
};

export default BufferControls;
