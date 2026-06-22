import { useAnalysis } from '../hooks/useAnalysis';

const StatsPanel = () => {
  const { analysisData } = useAnalysis();

  const parcelArea = analysisData?.parcel_area || 0;
  const buildableArea = analysisData?.buildable_area || 0;
  const excludedArea = analysisData?.excluded_area || 0;
  const breakdown = analysisData?.breakdown || [];

  return (
    <div className="stats-panel">
      <div className="stats-container">
        <div className="stat-box">
          <span className="stat-label">Parcel Area</span>
          <span className="stat-value">{parcelArea.toFixed(2)} acres</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Buildable Area</span>
          <span className="stat-value text-success">{buildableArea.toFixed(2)} acres</span>
        </div>
        <div className="stat-box">
          <span className="stat-label">Excluded Area</span>
          <span className="stat-value text-danger">{excludedArea.toFixed(2)} acres</span>
        </div>
      </div>

      <div className="breakdown-section">
        <h3>Breakdown</h3>
        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Layer</th>
              <th>Removed Area</th>
              <th>Why</th>
            </tr>
          </thead>
          <tbody>
            {breakdown.length > 0 ? (
              breakdown.map((item, idx) => (
                <tr key={idx}>
                  <td className="layer-name">{item.layer_name.replace('_', ' ').toUpperCase()}</td>
                  <td>{Number(item.removed_area).toFixed(2)} acres</td>
                  <td className="reason-text">{item.reason}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="3" className="text-center">No data available</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StatsPanel;
