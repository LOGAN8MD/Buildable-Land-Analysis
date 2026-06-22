import { useRef, useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import { useAnalysis } from '../hooks/useAnalysis';
import { customDrawStyles } from '../utils/drawStyles';

const MapView = () => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const draw = useRef(null);
  const selectParcelRef = useRef(null);

  const {
    analysisData,
    layerVisibility,
    drawMode,
    drawActivation,
    excludeArea,
    restoreArea,
    parcels,
    selectParcel,
  } = useAnalysis();

  useEffect(() => {
    selectParcelRef.current = selectParcel;
  }, [selectParcel]);

  // Initialize Map
  useEffect(() => {
    if (map.current) return;

    const currentMap = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [-122.395, 37.805],
      zoom: 12,
    });
    map.current = currentMap;

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    // Initialize MapboxDraw
    draw.current = new MapboxDraw({
      displayControlsDefault: false,
      controls: {
        polygon: true,
        trash: true,
      },
      defaultMode: 'simple_select',
      styles: customDrawStyles,
    });

    map.current.addControl(draw.current, 'top-right');

    map.current.on('load', () => {
      const emptyGeoJSON = { type: 'FeatureCollection', features: [] };

      // 1. Add Sources
      map.current.addSource('parcel', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('parcel-candidates', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('buildable', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('excluded', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('wetlands', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('floodzones', { type: 'geojson', data: emptyGeoJSON });
      map.current.addSource('buildings', { type: 'geojson', data: emptyGeoJSON });

      // 2. Add Layers
      map.current.addLayer({
        id: 'parcel-candidates-layer',
        type: 'line',
        source: 'parcel-candidates',
        paint: {
          'line-color': '#38bdf8',
          'line-width': 2,
          'line-opacity': 0.75,
          'line-dasharray': [2, 2],
        },
      });

      map.current.addLayer({
        id: 'parcel-layer',
        type: 'line',
        source: 'parcel',
        paint: { 'line-color': '#ffffff', 'line-width': 2 },
      });

      map.current.addLayer({
        id: 'wetlands-layer',
        type: 'fill',
        source: 'wetlands',
        paint: { 'fill-color': '#3b82f6', 'fill-opacity': 0.5 },
      });

      map.current.addLayer({
        id: 'floodzones-layer',
        type: 'fill',
        source: 'floodzones',
        paint: { 'fill-color': '#a855f7', 'fill-opacity': 0.5 },
      });

      map.current.addLayer({
        id: 'buildings-layer',
        type: 'fill',
        source: 'buildings',
        paint: { 'fill-color': '#f97316', 'fill-opacity': 0.5 },
      });

      map.current.addLayer({
        id: 'buildable-layer',
        type: 'fill',
        source: 'buildable',
        paint: { 'fill-color': '#10b981', 'fill-opacity': 0.5 },
      });

      map.current.addLayer({
        id: 'excluded-layer',
        type: 'fill',
        source: 'excluded',
        paint: { 'fill-color': '#ef4444', 'fill-opacity': 0.5 },
      });
      map.current.moveLayer('parcel-candidates-layer');
      map.current.moveLayer('parcel-layer');

      map.current.on('mouseenter', 'parcel-layer', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'parcel-layer', () => {
        map.current.getCanvas().style.cursor = '';
      });
      map.current.on('click', 'parcel-layer', (event) => {
        new maplibregl.Popup()
          .setLngLat(event.lngLat)
          .setHTML('<strong>Selected parcel</strong>')
          .addTo(map.current);
      });
      map.current.on('mouseenter', 'parcel-candidates-layer', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'parcel-candidates-layer', () => {
        map.current.getCanvas().style.cursor = '';
      });
      map.current.on('click', 'parcel-candidates-layer', (event) => {
        const parcelId = event.features?.[0]?.properties?.parcel_id;
        if (parcelId) {
          selectParcelRef.current?.(parcelId);
        }
      });
    });

    // Cleanup on unmount
    return () => {
      currentMap.remove();
      if (map.current === currentMap) {
        map.current = null;
      }
    };
  }, []);

  // Show all available parcels as clickable outlines.
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;
    const updateCandidates = () => {
      const source = currentMap.getSource('parcel-candidates');
      if (source) {
        source.setData({
          type: 'FeatureCollection',
          features: parcels.map((parcel) => ({
            type: 'Feature',
            properties: {
              parcel_id: parcel.parcel_id,
              property_id: parcel.property_id,
            },
            geometry: parcel.geometry,
          })),
        });
      }
    };
    if (currentMap.isStyleLoaded()) updateCandidates();
    else currentMap.once('load', updateCandidates);
    return () => currentMap.off('load', updateCandidates);
  }, [parcels]);

  // Sync GeoJSON Data
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const updateSourceData = () => {
      const emptyGeoJSON = { type: 'FeatureCollection', features: [] };

      const setSource = (sourceId, data) => {
        const source = currentMap.getSource(sourceId);
        if (source) {
          source.setData(data || emptyGeoJSON);
        }
      };

      setSource('parcel', analysisData.parcel_geometry);
      setSource('buildable', analysisData.buildable_geometry);
      setSource('excluded', analysisData.excluded_geometry);
      setSource('wetlands', analysisData.constraint_geometries?.wetlands);
      setSource('floodzones', analysisData.constraint_geometries?.floodzones);
      setSource('buildings', analysisData.constraint_geometries?.buildings);

      const coordinates = [];
      const collectCoordinates = (value) => {
        if (!Array.isArray(value)) return;
        if (value.length >= 2 && value.every((item) => typeof item === 'number')) {
          coordinates.push(value);
          return;
        }
        value.forEach(collectCoordinates);
      };
      collectCoordinates(analysisData.parcel_geometry?.coordinates);
      if (coordinates?.length) {
        const bounds = coordinates.reduce(
          (result, coordinate) => result.extend(coordinate),
          new maplibregl.LngLatBounds(coordinates[0], coordinates[0])
        );
        currentMap.fitBounds(bounds, { padding: 60, maxZoom: 16 });
      }
    };

    if (currentMap.isStyleLoaded()) {
      updateSourceData();
    } else {
      currentMap.once('load', updateSourceData);
    }

    return () => {
      if (currentMap) currentMap.off('load', updateSourceData);
    };
  }, [analysisData]);

  // Sync Layer Visibility
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const updateVisibility = () => {
      const toggleLayer = (layerId, isVisible) => {
        if (currentMap.getLayer(layerId)) {
          currentMap.setLayoutProperty(
            layerId,
            'visibility',
            isVisible ? 'visible' : 'none'
          );
        }
      };

      toggleLayer('parcel-layer', layerVisibility.parcel);
      toggleLayer('buildable-layer', layerVisibility.buildable);
      toggleLayer('excluded-layer', layerVisibility.excluded);
      toggleLayer('wetlands-layer', layerVisibility.wetlands);
      toggleLayer('floodzones-layer', layerVisibility.floodzones);
      toggleLayer('buildings-layer', layerVisibility.buildings);
    };

    if (currentMap.isStyleLoaded()) {
      updateVisibility();
    } else {
      currentMap.once('load', updateVisibility);
    }

    return () => {
      if (currentMap) currentMap.off('load', updateVisibility);
    };
  }, [layerVisibility]);

  useEffect(() => {
    if (drawActivation > 0 && draw.current) {
      draw.current.changeMode('draw_polygon');
    }
  }, [drawActivation]);

  // Handle Draw Events
  useEffect(() => {
    const currentMap = map.current;
    if (!currentMap) return;

    const handleDraw = async (event) => {
      if (!draw.current) return;

      const data = { type: 'FeatureCollection', features: event.features };

      // Trigger the appropriate API call based on drawMode
      let applied = false;
      if (drawMode === 'exclude') {
        applied = await excludeArea(data);
      } else if (drawMode === 'restore') {
        applied = await restoreArea(data);
      }
      if (applied) {
        draw.current.deleteAll();
      }
    };

    currentMap.on('draw.create', handleDraw);

    return () => {
      if (currentMap) {
        currentMap.off('draw.create', handleDraw);
      }
    };
  }, [drawMode, excludeArea, restoreArea]);

  return <div ref={mapContainer} className="map-container" style={{ width: '100%', height: '100%' }} />;
};

export default MapView;
