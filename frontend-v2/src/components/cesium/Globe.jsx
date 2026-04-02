import React from 'react';
import { Viewer, Entity, PointGraphics, EntityDescription, Cesium3DTileset } from 'resium';
import { Cartesian3, Color } from 'cesium';

const CesiumGlobe = ({ detectionEvents }) => {
  return (
    <div className="w-full h-full relative overflow-hidden rounded-3xl border border-white/10 shadow-2xl">
      <Viewer 
        full 
        timeline={false} 
        animation={false} 
        baseLayerPicker={false}
        navigationHelpButton={false}
        geocoder={false}
        infoBox={true}
        style={{
            width: '100%',
            height: '100%',
        }}
      >
        {/* Advanced 3D Tileset (e.g. Photogrammetry or OSM Buildings) */}
        <Cesium3DTileset 
            url="https://assets.ion.cesium.com/google-photorealistic-3d-tiles/tileset.json"
            onReady={(tileset) => {
                // Apply tactical styling
            }}
        />

        {/* Change Detection Markers */}
        {detectionEvents?.map((event, index) => (
          <Entity
            key={index}
            name={event.type}
            position={Cartesian3.fromDegrees(event.lng, event.lat, 100)}
          >
            <PointGraphics 
                pixelSize={12} 
                color={event.type === 'Deforestation' ? Color.RED : Color.CYAN} 
                outlineColor={Color.WHITE}
                outlineWidth={2}
            />
            <EntityDescription>
               <div className="p-2 text-sm">
                  <h4 className="font-bold border-b border-white/20 mb-2">{event.type} Detected</h4>
                  <p>Area: {event.area}m²</p>
                  <p>Confidence: {(event.confidence * 100).toFixed(1)}%</p>
                  <button className="mt-2 w-full bg-blue-600 text-white rounded py-1">View Timeline</button>
               </div>
            </EntityDescription>
          </Entity>
        ))}

        {/* Tactical HUD Overlay (CSS-based) */}
        <div className="absolute top-8 left-8 p-6 glass rounded-2xl flex flex-col gap-4 pointer-events-none">
            <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-bold tracking-[0.2em] text-white/60">LIVE TACTICAL FEED</span>
            </div>
            <div className="flex flex-col gap-1">
                <h2 className="text-2xl font-black tracking-tighter">STARSHIELD <span className="text-blue-500">v2.0</span></h2>
                <p className="text-[10px] text-white/30 uppercase font-bold tracking-widest">Global Multi-Modal Intelligence</p>
            </div>
        </div>
      </Viewer>
    </div>
  );
};

export default CesiumGlobe;
