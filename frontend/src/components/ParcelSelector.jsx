import { useAnalysis } from '../hooks/useAnalysis';

const ParcelSelector = () => {
  const { parcels, selectedParcelId, selectParcel, loading } = useAnalysis();
  const selectedParcel = parcels.find((item) => item.parcel_id === selectedParcelId);

  return (
    <section className="parcel-selector-section">
      <label htmlFor="parcel-selector">Select Parcel</label>
      <select
        id="parcel-selector"
        value={selectedParcelId}
        onChange={(event) => selectParcel(event.target.value)}
        disabled={loading || parcels.length === 0}
      >
        {parcels.map((parcel) => (
          <option key={parcel.parcel_id} value={parcel.parcel_id}>
            {parcel.property_id} - {parcel.address}
          </option>
        ))}
      </select>
      {selectedParcel && (
        <p className="parcel-meta">
          {selectedParcel.land_type} | {selectedParcel.source_acres.toFixed(2)} source acres
        </p>
      )}
    </section>
  );
};

export default ParcelSelector;
