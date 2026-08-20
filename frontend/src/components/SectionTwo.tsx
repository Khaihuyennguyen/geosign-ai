import { ChevronRight, FileText } from 'lucide-react';
import { Reveal } from './Reveal';

interface CapabilityItem {
  index: string;
  title: string;
  body: string;
}

interface SectionTwoProps {
  onLaunchScout?: () => void;
}

export const SectionTwo = ({ onLaunchScout }: SectionTwoProps) => {
  const capabilities: CapabilityItem[] = [
    {
      index: '01',
      title: '500-ft Buffer Exclusion Engine',
      body: 'Enforces Texas Transportation Code § 391.031 by calculating 500-foot buffer exclusion zones around all existing registered billboard structures.',
    },
    {
      index: '02',
      title: 'Gemini 3.5 Multimodal Satellite Vision',
      body: 'Inspects high-resolution aerial imagery to detect mature tree canopy occlusion, 300m driver approach cones at 65-75 mph, and utility power line access.',
    },
    {
      index: '03',
      title: 'Instant Municipal Permits & Leases',
      body: 'Compiles ready-to-file Municipal Sign Permit application packages and Landowner Ground Lease Decks with TCAD parcel valuations in 90 seconds.',
    },
  ];

  return (
    <section className="min-h-screen supports-[height:100svh]:min-h-[100svh] flex flex-col justify-between px-5 sm:px-8 md:px-12 pt-24 sm:pt-28 pb-12 md:pb-16 relative">
      {/* Top row */}
      <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between w-full">
        {/* Left badge */}
        <Reveal delay={120}>
          <div className="border-l-2 border-emerald-400 bg-white/15 px-3 py-1.5 backdrop-blur-md inline-block font-mono text-[11px] uppercase tracking-[0.15em] text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.8)]">
            Autonomous Geospatial Engine
          </div>
        </Reveal>

        {/* Right copy */}
        <Reveal delay={220} className="max-w-md sm:text-right">
          <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] font-normal">
            Our AI fleet doesn't just scan maps — it solves spatial spacing geometry, audits satellite sightlines, and delivers qualified billboard land.
          </p>
        </Reveal>
      </div>

      {/* Bottom area */}
      <div className="flex-1 flex flex-col justify-end gap-12 md:flex-row md:items-end md:justify-between md:gap-16 mt-16 sm:mt-24">
        {/* Left column */}
        <div className="max-w-xl">
          {/* H2 */}
          <Reveal delay={180}>
            <h2 className="text-5xl sm:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-tight text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.9)]">
              Turn aerial imagery
              <br />
              into revenue.
            </h2>
          </Reveal>

          {/* Body */}
          <Reveal delay={320}>
            <p className="mt-6 max-w-md text-sm sm:text-base text-white/90 drop-shadow-[0_2px_6px_rgba(0,0,0,0.85)] leading-relaxed">
              From raw TxDOT GIS coordinate meshes to ready-to-file municipal sign permits and landowner ground lease decks — GeoSignAI uncovers high-yield billboard locations before competitors even open a map.
            </p>
          </Reveal>

          {/* CTAs */}
          <Reveal delay={420}>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <button
                onClick={onLaunchScout}
                className="inline-flex items-center gap-1.5 rounded-full bg-white px-5 py-2.5 text-xs sm:text-sm font-medium text-black hover:bg-white/85 transition-colors duration-300 shadow-md cursor-pointer"
              >
                <span>Launch Autonomous Scout</span>
                <ChevronRight size={14} />
              </button>
              <button
                onClick={onLaunchScout}
                className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 backdrop-blur-md px-5 py-2.5 text-xs sm:text-sm text-white hover:bg-white/20 transition-colors duration-300 cursor-pointer"
              >
                <FileText size={14} className="text-emerald-400" />
                <span>Sample Feasibility PDF</span>
              </button>
            </div>
          </Reveal>
        </div>

        {/* Right — frosted capability panel */}
        <div className="w-full max-w-md rounded-2xl border border-white/15 bg-white/10 backdrop-blur-md px-5 sm:px-6 shadow-2xl">
          {capabilities.map((item, i) => (
            <Reveal
              key={item.index}
              delay={300 + i * 110}
              className={`py-5 flex gap-5 group cursor-default ${
                i !== capabilities.length - 1 ? 'border-b border-white/15' : ''
              }`}
            >
              <div className="font-mono text-[11px] tracking-[0.15em] text-emerald-400 pt-1 font-semibold">
                {item.index}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="text-base sm:text-lg font-medium text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
                    {item.title}
                  </h3>
                  <ChevronRight
                    size={16}
                    className="text-white/40 group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all duration-300"
                  />
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-white/80 drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
                  {item.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
};
