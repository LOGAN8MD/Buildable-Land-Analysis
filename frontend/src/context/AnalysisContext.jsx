import { useState } from 'react';
import { analysisApi } from '../api/analysisApi';
import { AnalysisContext } from './analysisContextStore';

export const AnalysisProvider = ({ children }) => {
  const [analysisData, setAnalysisData] = useState({
    parcel_area: 0,
    excluded_area: 0,
    buildable_area: 0,
    breakdown: [],
    parcel_geometry: null,
    constraint_geometries: {},
    buildable_geometry: null,
    excluded_geometry: null,
  });

  const [buffers, setBuffers] = useState({
    wetlands: 50,
    buildings: 20,
    floodzones: 0,
  });

  const [parcels, setParcels] = useState([]);
  const [selectedParcelId, setSelectedParcelId] = useState('parcel');

  const [layerVisibility, setLayerVisibility] = useState({
    parcel: true,
    wetlands: true,
    floodzones: true,
    buildings: true,
    buildable: true,
    excluded: true,
  });

  const [drawMode, setDrawModeState] = useState('exclude'); // 'exclude' | 'restore'
  const [drawActivation, setDrawActivation] = useState(0);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async (parcelId = selectedParcelId, bufferOverride = buffers) => {
    try {
      setLoading(true);
      const payload = {
        parcel_id: String(parcelId),
        constraints: ['wetlands', 'floodzones', 'buildings'],
        buffers: bufferOverride,
      };
      const response = await analysisApi.analyzeParcel(payload);
      if (response && response.buildable_geometry) {
        setAnalysisData(response);
      } else {
        console.warn("Analysis response is missing geometry data:", response);
      }
    } catch (err) {
      console.error('Failed to run analysis:', err.message || err);
      alert('Analysis Error: ' + (err.message || 'Unknown error occurred.'));
    } finally {
      setLoading(false);
    }
  };

  const fetchParcels = async () => {
    try {
      setLoading(true);
      const availableParcels = await analysisApi.listParcels();
      setParcels(availableParcels);
      const initialParcel = availableParcels.some((item) => item.parcel_id === 'parcel')
        ? 'parcel'
        : availableParcels[0]?.parcel_id;
      if (initialParcel) {
        setSelectedParcelId(initialParcel);
        await runAnalysis(initialParcel);
      }
    } catch (err) {
      console.error('Failed to load parcels:', err.message || err);
      alert('Parcel Error: ' + (err.message || 'Failed to load available parcels.'));
    } finally {
      setLoading(false);
    }
  };

  const selectParcel = async (parcelId) => {
    setSelectedParcelId(parcelId);
    setDrawModeState('exclude');
    await runAnalysis(parcelId);
  };

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const config = await analysisApi.getConfig();
      if (config && config.buffers) {
        setBuffers(config.buffers);
      }
    } catch (err) {
      console.error('Failed to fetch config:', err.message || err);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async (newBuffers) => {
    try {
      setLoading(true);
      setBuffers(newBuffers);
      await runAnalysis(selectedParcelId, newBuffers);
    } catch (err) {
      console.error('Failed to save config:', err.message || err);
      alert('Config Error: ' + (err.message || 'Failed to save config.'));
    } finally {
      setLoading(false);
    }
  };

  const updateBuffers = (newBuffers) => {
    // Only updates local state. Caller should invoke saveConfig when ready to persist.
    setBuffers((prev) => ({ ...prev, ...newBuffers }));
  };

  const toggleLayer = (layerName) => {
    setLayerVisibility((prev) => ({
      ...prev,
      [layerName]: !prev[layerName],
    }));
  };

  const setDrawMode = (mode) => {
    setDrawModeState(mode);
    setDrawActivation((value) => value + 1);
  };

  const excludeArea = async (geometry) => {
    if (!analysisData.parcel_geometry?.type || !analysisData.buildable_geometry?.type) {
      alert('Run the parcel analysis before drawing an exclusion.');
      return false;
    }
    try {
      setLoading(true);
      const updatedData = await analysisApi.excludeArea({
        geometry,
        current_buildable: analysisData.buildable_geometry,
        current_excluded: analysisData.excluded_geometry,
        parcel_geometry: analysisData.parcel_geometry,
        constraint_geometries: analysisData.constraint_geometries,
        breakdown: analysisData.breakdown
      });

      if (updatedData && updatedData.buildable_geometry) {
        setAnalysisData(updatedData);
      }
      return true;
    } catch (err) {
      console.error('Failed to exclude area:', err.message || err);
      alert('Exclude Area Error: ' + (err.message || 'Unknown error occurred.'));
      return false;
    } finally {
      setLoading(false);
    }
  };

  const restoreArea = async (geometry) => {
    if (!analysisData.parcel_geometry?.type || !analysisData.excluded_geometry?.type) {
      alert('Run the parcel analysis before drawing a restoration.');
      return false;
    }
    try {
      setLoading(true);
      const updatedData = await analysisApi.restoreArea({
        geometry,
        current_buildable: analysisData.buildable_geometry,
        current_excluded: analysisData.excluded_geometry,
        parcel_geometry: analysisData.parcel_geometry,
        constraint_geometries: analysisData.constraint_geometries,
        breakdown: analysisData.breakdown
      });
      if (updatedData && updatedData.buildable_geometry) {
        setAnalysisData(updatedData);
      }
      return true;
    } catch (err) {
      console.error('Failed to restore area:', err.message || err);
      alert('Restore Area Error: ' + (err.message || 'Unknown error occurred.'));
      return false;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnalysisContext.Provider
      value={{
        analysisData,
        parcels,
        selectedParcelId,
        buffers,
        layerVisibility,
        drawMode,
        drawActivation,
        loading,
        runAnalysis,
        fetchParcels,
        selectParcel,
        updateBuffers,
        fetchConfig,
        saveConfig,
        toggleLayer,
        setDrawMode,
        excludeArea,
        restoreArea,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
};
