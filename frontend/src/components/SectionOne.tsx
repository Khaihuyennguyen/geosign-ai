import { ChevronRight, Satellite, MapPin } from 'lucide-react';
import { Reveal } from './Reveal';

interface SectionOneProps {
  onLaunchScout?: () => void;
}

export const SectionOne = ({ onLaunchScout }: SectionOneProps) => {
  const services = [
    '/ 500-FT SPATIAL BUFFER MATH',
    '/ GEMINI 3.5 MULTIMODAL SATELLITE VISION',
    '/ AUTONOMOUS MUNICIPAL PERMIT FLEET',
  ];

  return (
    <section className="min-h-screen supports-[height:100svh]:min-h-[100svh] flex flex-col justify-between px-5 sm:px-8 md:px-12 pt-24 sm:pt-28 pb-12 md:pb-16 relative">
      {/* Top row */}
      <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between w-full">
        {/* Left — service list */}
        <div className="flex flex-col gap-2">
          {services.map((service, i) => (
            <Reveal key={service} delay={150 + i * 120}>
              <div className="font-mono text-xs uppercase tracking-[0.15em] text-white/95 drop-shadow-[0_2px_4px_rgba(0,0,0,0.85)] flex items-center gap-2">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]"></span>
                {service}
              </div>
            </Reveal>
          ))}
        </div>

        {/* Right — intro */}
        <Reveal delay={300} className="max-w-md sm:text-right">
          <p className="text-lg sm:text-xl leading-relaxed text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] font-normal">
            We turn a 6-month, manual billboard site scouting process into a 90-second autonomous geospatial pipeline for the $40B Out-of-Home market.
          </p>
        </Reveal>
      </div>

      {/* Bottom row */}
      <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between w-full mt-16 sm:mt-24">
        {/* Left column */}
        <div className="max-w-xl">
          {/* Badge */}
          <Reveal delay={150}>
            <div className="border-l-2 border-emerald-400 bg-white/15 px-3 py-1.5 backdrop-blur-md inline-block mb-5 font-mono text-[11px] uppercase tracking-[0.15em] text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.8)]">
              440+ Corridors & Parcels Sited Across Texas
            </div>
          </Reveal>

          {/* H1 */}
          <Reveal delay={280}>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-normal leading-[1.05] tracking-tight text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.9)]">
              Scout. Reason.
              <br />
              Permit.
            </h1>
          </Reveal>
        </div>

        {/* Right — glass contact card */}
        <Reveal delay={420} className="w-full sm:w-auto">
          <div className="flex items-center gap-4 rounded-xl bg-white/15 p-3.5 backdrop-blur-md border border-white/20 shadow-xl max-w-sm sm:max-w-none">
            {/* Tech Parcel Preview Box */}
            <div className="h-24 w-24 rounded-lg bg-black/40 border border-white/20 flex flex-col items-center justify-center p-2 text-center relative overflow-hidden flex-shrink-0">
              <Satellite size={22} className="text-emerald-400 mb-1 z-10" />
              <span className="font-mono text-[9px] uppercase tracking-wider text-emerald-300 font-semibold z-10">
                TCAD #021920
              </span>
              <span className="font-mono text-[8px] text-white/80 z-10 drop-shadow">
                128,400 AADT
              </span>
              <div className="absolute bottom-1 right-1 flex h-1.5 w-1.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
              </div>
            </div>

            <div className="flex flex-col gap-1.5 pr-2">
              <div className="flex items-center gap-1.5">
                <MapPin size={14} className="text-emerald-400" />
                <span className="text-sm font-medium text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
                  I-35 & US-183 Corridors
                </span>
              </div>
              <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-white/70">
                TxDOT § 391.031 Verified
              </span>
              <button
                onClick={onLaunchScout}
                className="mt-1.5 inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-xs font-medium text-black hover:bg-white/85 transition-colors duration-300 w-fit shadow-md cursor-pointer"
              >
                <span>Launch Autonomous Scout</span>
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
};
