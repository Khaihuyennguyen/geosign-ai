import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import {
  Satellite,
  FileText,
  Compass,
  ArrowLeft,
  ShieldCheck,
  TrendingUp,
  Car,
  Eye,
  Download,
  RotateCcw,
  CheckCircle2,
} from 'lucide-react';

interface Parcel {
  parcel_id: string;
  name?: string;
  address: string;
  owner_name: string;
  zoning: string;
  aadt_traffic: number;
  coordinates: [number, number];
  lot_boundary?: number[][];
  county?: string;
  frontage_side?: string;
  has_dense_trees: boolean;
  is_qualified: boolean;
  disqualification_reasons: string[];
  min_distance_to_sign_feet: number;
  nearest_billboard_permit: string;
  nearest_operator: string;
  nearest_coordinates: [number, number];
  spacing_passed: boolean;
  spacing_margin_feet: number;
  is_commercial_zoning: boolean;
  tree_canopy_present: boolean;
  visibility_score: number;
  obstruction_level: string;
  ai_visual_justification: string;
  est_annual_ad_revenue: number;
  pdf_available: boolean;
}

interface ScoutData {
  corridor_id: string;
  corridor_name: string;
  total_evaluated: number;
  qualified_count: number;
  disqualified_count: number;
  parcels: Parcel[];
  highway_centerline: [number, number][];
  existing_billboards: Array<{ id: string; permit_number: string; operator: string; coordinates: [number, number] }>;
  cadastral_polygons?: Array<{ id: string; name: string; zoning: string; coordinates: [number, number][] }>;
  agent_thought_traces: string[];
}

interface MissionControlProps {
  onBackToLanding: () => void;
}

export const MissionControl = ({ onBackToLanding }: MissionControlProps) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{
    darkTile: L.TileLayer;
    satTile: L.TileLayer;
    parcels: L.LayerGroup;
    buffers: L.LayerGroup;
    billboards: L.LayerGroup;
    highway: L.Polyline | null;
    activeHighlight: L.Polygon | null;
  }>({
    darkTile: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
      maxZoom: 19,
    }),
    satTile: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri World Imagery',
      maxZoom: 19,
    }),
    parcels: L.layerGroup(),
    buffers: L.layerGroup(),
    billboards: L.layerGroup(),
    highway: null,
    activeHighlight: null,
  });

  const [baseMap, setBaseMap] = useState<'dark' | 'satellite'>('dark');
  const [selectedParcel, setSelectedParcel] = useState<Parcel | null>(null);
  const [scoutData, setScoutData] = useState<ScoutData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCorridor, setActiveCorridor] = useState('I35-50Mile-Regional');
  const [showBuffers, setShowBuffers] = useState(true);
  const [showParcels, setShowParcels] = useState(true);
  const [pdfDownloading, setPdfDownloading] = useState(false);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [30.265, -97.734],
      zoom: 12,
      layers: [layersRef.current.darkTile, layersRef.current.parcels, layersRef.current.buffers, layersRef.current.billboards],
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Fetch Scout Data from FastAPI Backend
  const runScout = async (corridorId = activeCorridor) => {
    setLoading(true);
    try {
      const res = await fetch('/api/scout/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          corridor_id: corridorId,
          min_traffic: 25000,
          min_spacing_feet: 500.0,
        }),
      });

      if (!res.ok) throw new Error('Failed to run scout');
      const data: ScoutData = await res.json();
      setScoutData(data);
      renderMapData(data);

      const topQualified = data.parcels.find((p) => p.is_qualified && !p.tree_canopy_present) || data.parcels[0];
      if (topQualified) {
        selectParcel(topQualified);
      }
    } catch (err) {
      console.error('Error connecting to backend scout agent:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runScout(activeCorridor);
  }, [activeCorridor]);

  // Switch Base Map
  const toggleBaseMap = (type: 'dark' | 'satellite') => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (type === 'satellite') {
      map.removeLayer(layersRef.current.darkTile);
      map.addLayer(layersRef.current.satTile);
      setBaseMap('satellite');
    } else {
      map.removeLayer(layersRef.current.satTile);
      map.addLayer(layersRef.current.darkTile);
      setBaseMap('dark');
    }
  };

  // Render Map Geometries
  const renderMapData = (data: ScoutData) => {
    const map = mapInstanceRef.current;
    if (!map) return;

    layersRef.current.parcels.clearLayers();
    layersRef.current.buffers.clearLayers();
    layersRef.current.billboards.clearLayers();
    if (layersRef.current.highway) {
      map.removeLayer(layersRef.current.highway);
    }

    // 1. Highway Centerline
    if (data.highway_centerline && data.highway_centerline.length > 0) {
      const latlngs = data.highway_centerline.map((c) => [c[1], c[0]] as [number, number]);
      const highway = L.polyline(latlngs, {
        color: '#06b6d4',
        weight: 3.5,
        opacity: 0.85,
        dashArray: '8, 6',
      }).addTo(map);
      layersRef.current.highway = highway;
      map.fitBounds(highway.getBounds(), { padding: [40, 40] });
    }

    // 2. Existing Billboards + 500ft Buffer Circles
    data.existing_billboards.forEach((bb) => {
      const lat = bb.coordinates[1];
      const lng = bb.coordinates[0];

      // 500-ft buffer (152.4 meters)
      const buffer = L.circle([lat, lng], {
        radius: 152.4,
        color: '#a855f7',
        fillColor: '#a855f7',
        fillOpacity: 0.12,
        weight: 1.5,
        dashArray: '4, 4',
      });
      layersRef.current.buffers.addLayer(buffer);

      // Billboard Marker Icon
      const marker = L.circleMarker([lat, lng], {
        radius: 5,
        color: '#ffffff',
        fillColor: '#9333ea',
        fillOpacity: 1,
        weight: 1.5,
      });
      marker.bindPopup(`
        <div style="font-family: Inter, sans-serif; font-size: 11px;">
          <strong style="color: #c084fc;">TxDOT Registered Billboard</strong><br/>
          Permit: <b>${bb.permit_number}</b><br/>
          Operator: ${bb.operator}
        </div>
      `);
      layersRef.current.billboards.addLayer(marker);
    });

    // 3. Individual Commercial Parcels
    data.parcels.forEach((parcel) => {
      const lat = parcel.coordinates[1];
      const lng = parcel.coordinates[0];

      const isTreeRisk = parcel.is_qualified && parcel.tree_canopy_present;
      const fillColor = !parcel.is_qualified ? '#f43f5e' : isTreeRisk ? '#f59e0b' : '#10b981';
      const strokeColor = '#ffffff';

      // If polygon boundary available, render polygon
      if (parcel.lot_boundary && parcel.lot_boundary.length >= 3) {
        const polyCoords = parcel.lot_boundary.map((pt) => [pt[1], pt[0]] as [number, number]);
        const poly = L.polygon(polyCoords, {
          color: strokeColor,
          fillColor: fillColor,
          fillOpacity: 0.55,
          weight: 1.2,
        });

        poly.on('click', () => selectParcel(parcel));
        layersRef.current.parcels.addLayer(poly);
      }

      // Marker badge
      const marker = L.circleMarker([lat, lng], {
        radius: 6,
        color: '#ffffff',
        fillColor: fillColor,
        fillOpacity: 1,
        weight: 1.5,
      });

      marker.on('click', () => selectParcel(parcel));
      layersRef.current.parcels.addLayer(marker);
    });
  };

  // Select Parcel and Highlight
  const selectParcel = (parcel: Parcel) => {
    setSelectedParcel(parcel);
    const map = mapInstanceRef.current;
    if (!map) return;

    if (layersRef.current.activeHighlight) {
      map.removeLayer(layersRef.current.activeHighlight);
      layersRef.current.activeHighlight = null;
    }

    const lat = parcel.coordinates[1];
    const lng = parcel.coordinates[0];

    if (parcel.lot_boundary && parcel.lot_boundary.length >= 3) {
      const polyCoords = parcel.lot_boundary.map((pt) => [pt[1], pt[0]] as [number, number]);
      const highlight = L.polygon(polyCoords, {
        color: '#38bdf8',
        fillColor: '#38bdf8',
        fillOpacity: 0.75,
        weight: 3,
      }).addTo(map);
      layersRef.current.activeHighlight = highlight;
    }

    map.panTo([lat, lng], { animate: true, duration: 0.5 });
  };

  // Download PDF Report
  const downloadPdf = async (parcelId: string) => {
    setPdfDownloading(true);
    try {
      const res = await fetch(`/api/parcels/${parcelId}/pdf`);
      if (!res.ok) throw new Error('PDF Generation Failed');
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Feasibility_Report_${parcelId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      console.error('PDF download failed:', e);
    } finally {
      setPdfDownloading(false);
    }
  };

  // Toggle Buffer Visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    if (showBuffers) {
      map.addLayer(layersRef.current.buffers);
      map.addLayer(layersRef.current.billboards);
    } else {
      map.removeLayer(layersRef.current.buffers);
      map.removeLayer(layersRef.current.billboards);
    }
  }, [showBuffers]);

  // Toggle Parcel Visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;
    if (showParcels) {
      map.addLayer(layersRef.current.parcels);
    } else {
      map.removeLayer(layersRef.current.parcels);
    }
  }, [showParcels]);

  return (
    <div className="h-screen w-screen bg-[#07090e] text-gray-100 flex flex-col overflow-hidden font-sans select-none">
      {/* Top Mission Control Navigation */}
      <header className="bg-[#0c1017] border-b border-white/15 px-4 sm:px-6 py-2.5 flex items-center justify-between shadow-2xl z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToLanding}
            className="flex items-center gap-1.5 rounded-lg bg-white/10 hover:bg-white/20 border border-white/15 px-3 py-1.5 text-xs font-semibold text-white transition-colors duration-200 cursor-pointer"
            title="Return to Landing Page"
          >
            <ArrowLeft size={14} />
            <span>Landing Page</span>
          </button>

          <div className="h-5 w-px bg-white/15 mx-1" />

          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-md bg-emerald-500/20 border border-emerald-500/40 text-emerald-400">
              <Satellite size={18} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white tracking-tight">GeoSignAI Mission Control</span>
                <span className="font-mono text-[9px] uppercase tracking-wider text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded border border-emerald-500/40 font-bold">
                  Fleet Online
                </span>
                <span className="hidden md:inline-block font-mono text-[9px] uppercase tracking-wider text-blue-400 bg-blue-500/20 px-1.5 py-0.5 rounded border border-blue-500/40">
                  Gemini 3.5 Flash
                </span>
              </div>
              <p className="text-[10px] text-gray-400">Autonomous Multimodal Billboard Siting & Permitting Fleet</p>
            </div>
          </div>
        </div>

        {/* Action Controls & Switchers */}
        <div className="flex items-center gap-2.5">
          {/* Corridor Select Dropdown */}
          <select
            value={activeCorridor}
            onChange={(e) => setActiveCorridor(e.target.value)}
            className="bg-[#111827] border border-white/15 text-xs text-white rounded-lg px-2.5 py-1 focus:outline-none focus:border-emerald-500"
          >
            <option value="I35-50Mile-Regional">I-35 50-Mile Regional (Austin/San Marcos)</option>
          </select>

          {/* Base Map Switcher */}
          <div className="flex bg-[#111827] p-0.5 rounded-lg border border-white/15 text-xs">
            <button
              onClick={() => toggleBaseMap('dark')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition cursor-pointer ${
                baseMap === 'dark' ? 'bg-emerald-500 text-gray-950 shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              Dark Map
            </button>
            <button
              onClick={() => toggleBaseMap('satellite')}
              className={`px-2.5 py-1 rounded-md text-xs font-semibold transition cursor-pointer ${
                baseMap === 'satellite' ? 'bg-emerald-500 text-gray-950 shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              Satellite
            </button>
          </div>

          {/* Re-Run Scout */}
          <button
            onClick={() => runScout(activeCorridor)}
            disabled={loading}
            className="rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 px-3.5 py-1.5 text-xs font-bold text-gray-950 transition shadow-[0_0_15px_rgba(16,185,129,0.35)] flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
          >
            <RotateCcw size={13} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Scouting...' : 'Re-Run Scout'}</span>
          </button>
        </div>
      </header>

      {/* Main Grid Workspace */}
      <div className="flex-1 grid grid-cols-12 gap-3 p-3 overflow-hidden">
        {/* Left Map Viewport */}
        <div className="col-span-12 lg:col-span-7 bg-[#0c1017] border border-white/15 rounded-xl p-2.5 flex flex-col shadow-2xl relative">
          {/* Map Top Status Bar */}
          <div className="flex items-center justify-between pb-2 mb-1.5 border-b border-white/10 text-xs text-gray-400">
            <div className="flex items-center gap-3 text-[11px] flex-wrap">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 border border-white"></span> Qualified ({scoutData?.qualified_count || 0})
              </span>
              <span className="flex items-center gap-1 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-amber-500 border border-white"></span> Tree Risk
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-rose-500 border border-white"></span> Disqualified ({scoutData?.disqualified_count || 0})
              </span>
              <span className="flex items-center gap-1 text-purple-400">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span> 500ft Buffer
              </span>
            </div>

            {/* Layer Toggles */}
            <div className="flex items-center gap-2 text-[10px] font-mono">
              <label className="flex items-center gap-1 cursor-pointer hover:text-white">
                <input
                  type="checkbox"
                  checked={showBuffers}
                  onChange={(e) => setShowBuffers(e.target.checked)}
                  className="rounded accent-purple-500"
                />
                <span>Buffers</span>
              </label>
              <label className="flex items-center gap-1 cursor-pointer hover:text-white">
                <input
                  type="checkbox"
                  checked={showParcels}
                  onChange={(e) => setShowParcels(e.target.checked)}
                  className="rounded accent-emerald-500"
                />
                <span>Parcels</span>
              </label>
            </div>
          </div>

          {/* Leaflet Container */}
          <div className="flex-1 relative rounded-lg overflow-hidden border border-white/10">
            <div ref={mapContainerRef} className="w-full h-full" />
          </div>
        </div>

        {/* Right Telemetry & Dossier Sidebars */}
        <div className="col-span-12 lg:col-span-5 flex flex-col gap-3 overflow-hidden">
          {/* Live Agent Execution Trace Terminal */}
          <div className="bg-[#0c1017] border border-white/15 rounded-xl p-3.5 flex flex-col h-2/5 shadow-xl">
            <div className="flex items-center justify-between pb-2 mb-1.5 border-b border-white/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-gray-200 flex items-center gap-1.5">
                <Compass size={14} className="text-emerald-400" />
                <span>Live Agent Execution Trace</span>
              </h2>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-2 py-0.5 rounded font-mono font-bold">
                TXDOT GIS ONLINE
              </span>
            </div>

            <div className="flex-1 overflow-y-auto font-mono text-[11px] text-gray-300 space-y-1 p-2.5 bg-black/60 rounded-lg border border-white/10">
              {scoutData?.agent_thought_traces?.map((trace, i) => (
                <div
                  key={i}
                  className={`${
                    trace.includes('[VISION APPROVED]')
                      ? 'text-emerald-400 font-semibold'
                      : trace.includes('[VISION CAUTION]')
                      ? 'text-amber-400'
                      : trace.includes('[DISQUALIFIED]')
                      ? 'text-rose-400/80'
                      : 'text-gray-400'
                  }`}
                >
                  {trace}
                </div>
              )) || <div className="text-gray-500">Awaiting agent thought traces...</div>}
            </div>
          </div>

          {/* Site Feasibility Dossier & Proof Center */}
          <div className="bg-[#0c1017] border border-white/15 rounded-xl p-4 flex flex-col h-3/5 shadow-xl overflow-y-auto">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/10">
              <h2 className="text-xs font-bold uppercase tracking-wider text-gray-200 flex items-center gap-1.5">
                <FileText size={14} className="text-emerald-400" />
                <span>Site Feasibility Dossier</span>
              </h2>
              {selectedParcel && (
                <span
                  className={`text-[10px] px-2.5 py-0.5 rounded font-bold ${
                    selectedParcel.is_qualified
                      ? selectedParcel.tree_canopy_present
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                  }`}
                >
                  {selectedParcel.is_qualified
                    ? selectedParcel.tree_canopy_present
                      ? 'TREE VARIANCE REQUIRED'
                      : 'PERMIT READY'
                    : 'DISQUALIFIED'}
                </span>
              )}
            </div>

            {selectedParcel ? (
              <div className="space-y-3 flex-1 flex flex-col justify-between text-xs">
                {/* Header Summary */}
                <div className="bg-black/50 p-3 rounded-lg border border-white/10 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-white">{selectedParcel.parcel_id}</span>
                    <span className="font-mono text-[10px] text-emerald-400 font-semibold bg-emerald-500/15 px-2 py-0.5 rounded">
                      {selectedParcel.zoning}
                    </span>
                  </div>
                  <div className="text-gray-200 font-medium">{selectedParcel.address}</div>
                  <div className="text-gray-400 text-[11px]">Owner: <strong className="text-white">{selectedParcel.owner_name}</strong></div>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-black/40 p-2.5 rounded-lg border border-white/10">
                    <div className="text-[10px] text-gray-400 flex items-center gap-1">
                      <Car size={12} className="text-blue-400" />
                      <span>AADT Traffic Count</span>
                    </div>
                    <div className="font-mono text-sm font-bold text-white mt-0.5">
                      {selectedParcel.aadt_traffic.toLocaleString()} cars/day
                    </div>
                  </div>

                  <div className="bg-black/40 p-2.5 rounded-lg border border-white/10">
                    <div className="text-[10px] text-gray-400 flex items-center gap-1">
                      <TrendingUp size={12} className="text-emerald-400" />
                      <span>Est. Annual Ad Value</span>
                    </div>
                    <div className="font-mono text-sm font-bold text-emerald-400 mt-0.5">
                      ${selectedParcel.est_annual_ad_revenue.toLocaleString()} / yr
                    </div>
                  </div>

                  <div className="bg-black/40 p-2.5 rounded-lg border border-white/10">
                    <div className="text-[10px] text-gray-400 flex items-center gap-1">
                      <ShieldCheck size={12} className="text-purple-400" />
                      <span>Nearest Billboard</span>
                    </div>
                    <div className="font-mono text-xs font-bold text-white mt-0.5">
                      {selectedParcel.min_distance_to_sign_feet.toFixed(1)} ft (Req: 500ft)
                    </div>
                  </div>

                  <div className="bg-black/40 p-2.5 rounded-lg border border-white/10">
                    <div className="text-[10px] text-gray-400 flex items-center gap-1">
                      <Eye size={12} className="text-amber-400" />
                      <span>Visibility Score</span>
                    </div>
                    <div className="font-mono text-xs font-bold text-white mt-0.5">
                      {selectedParcel.visibility_score} / 100
                    </div>
                  </div>
                </div>

                {/* Gemini 3.5 Flash Multimodal Vision Report */}
                <div className="bg-black/50 p-2.5 rounded-lg border border-white/10 space-y-1">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 size={12} />
                    <span>Gemini 3.5 Flash Sightline Audit</span>
                  </div>
                  <p className="text-[11px] text-gray-300 leading-relaxed">
                    {selectedParcel.ai_visual_justification}
                  </p>
                </div>

                {/* Download Municipal PDF Package */}
                <button
                  onClick={() => downloadPdf(selectedParcel.parcel_id)}
                  disabled={pdfDownloading}
                  className="w-full rounded-lg bg-emerald-500 hover:bg-emerald-400 px-4 py-2.5 font-bold text-xs text-gray-950 transition shadow-[0_0_20px_rgba(16,185,129,0.35)] flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
                >
                  <Download size={14} />
                  <span>{pdfDownloading ? 'Compiling Official PDF...' : 'Download 1-Page Feasibility Report PDF'}</span>
                </button>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center text-gray-500 space-y-2">
                <Compass size={32} className="text-gray-600 animate-pulse" />
                <p className="text-xs">Click any parcel box on the map to inspect owner, sightlines, and permit package.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
