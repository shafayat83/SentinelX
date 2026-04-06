import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapView = ({ onAOISelected, resultGeoJSON }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [lng, setLng] = useState(34.8888);
  const [lat, setLat] = useState(31.2518);
  const [zoom, setZoom] = useState(13);

  useEffect(() => {
    if (map.current) return; // Initialize map only once

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [lng, lat],
      zoom: zoom,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
    
    // Add Satellite Layer (Public WMS example)
    map.current.on('load', () => {
      // Base Sentinel-2 Layer Placeholder
      // In production, we'd use a real Tiling service
      map.current.addSource('sentinel-2', {
        'type': 'raster',
        'tiles': [
          'https://services.sentinel-hub.com/ogc/wms/your-id?SERVICE=WMS&REQUEST=GetMap&LAYERS=TRUE-COLOR&BBOX={bbox-epsg-3857}&WIDTH=256&HEIGHT=256&FORMAT=image/png'
        ],
        'tileSize': 256
      });
      
      map.current.addLayer({
        'id': 'satellite',
        'type': 'raster',
        'source': 'sentinel-2',
        'paint': { 'raster-opacity': 0.6 }
      });
    });
  }, [lng, lat, zoom]);

  // Handle Detection Results Overlay
  useEffect(() => {
    if (!map.current || !resultGeoJSON) return;
    
    const sourceId = 'results-source';
    const layerId = 'results-layer';
    
    if (map.current.getSource(sourceId)) {
        map.current.getSource(sourceId).setData(JSON.parse(resultGeoJSON));
    } else {
        map.current.addSource(sourceId, {
            type: 'geojson',
            data: JSON.parse(resultGeoJSON)
        });
        
        map.current.addLayer({
            id: layerId,
            type: 'fill',
            source: sourceId,
            paint: {
                'fill-color': '#ef4444',
                'fill-opacity': 0.5,
                'fill-outline-color': '#ffffff'
            }
        });
    }
  }, [resultGeoJSON]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="map-container rounded-xl overflow-hidden shadow-2xl border border-white/5" />
      
      {/* HUD Info */}
      <div className="absolute bottom-6 left-6 p-4 glass rounded-lg pointer-events-none select-none">
        <h3 className="text-sm font-semibold text-white/80">Satellite Feed: Sentinel-2 L2A</h3>
        <p className="text-xs text-white/40">Resolution: 10m/px</p>
      </div>

      {/* Floating Controls Placeholder */}
      <div className="absolute top-6 left-6 flex flex-col gap-2">
         <button className="p-3 glass rounded-full hover:bg-white/10 transition-all text-white/80" title="Draw AOI">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>
         </button>
      </div>
    </div>
  );
};

export default MapView;
