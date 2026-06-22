import { useEffect } from 'react';
import MapView from '../components/MapView';
import Sidebar from '../components/Sidebar';
import { useAnalysis } from '../hooks/useAnalysis';

const Home = () => {
  const { fetchParcels } = useAnalysis();

  // Load parcel analysis automatically on mount
  useEffect(() => {
    fetchParcels();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="home-container">
      <Sidebar />
      <MapView />
    </div>
  );
};

export default Home;
