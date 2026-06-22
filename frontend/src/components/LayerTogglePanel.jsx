import { useAnalysis } from '../hooks/useAnalysis';

const LayerTogglePanel = () => {
  const { layerVisibility, toggleLayer } = useAnalysis();

  const layers = [
    { key: 'parcel', label: 'Parcel Boundary' },
    { key: 'buildable', label: 'Buildable Area' },
    { key: 'excluded', label: 'Excluded Area' },
    { key: 'wetlands', label: 'Wetlands' },
    { key: 'floodzones', label: 'Flood Zones' },
    { key: 'buildings', label: 'Buildings' },
  ];

  return (
    <div className="layer-toggle-section">
      <h3>Map Layers</h3>
      <div className="layer-toggle-list">
        {layers.map(({ key, label }) => (
          <label key={key} className="layer-toggle-item">
            <input
              type="checkbox"
              checked={layerVisibility[key]}
              onChange={() => toggleLayer(key)}
            />
            <span className="checkbox-custom"></span>
            <span className="layer-label">{label}</span>
          </label>
        ))}
      </div>
    </div>
  );
};

export default LayerTogglePanel;
