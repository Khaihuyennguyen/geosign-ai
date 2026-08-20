import { Satellite } from 'lucide-react';
import { Reveal } from './Reveal';

interface NavbarProps {
  onLaunchScout?: () => void;
}

export const Navbar = ({ onLaunchScout }: NavbarProps) => {
  const navLinks = [
    { label: 'Corridors', hasSuper: true, superText: '440', href: '#corridors' },
    { label: 'Spatial Engine', href: '#spatial-engine' },
    { label: 'Vision Agent', href: '#vision-agent' },
    { label: 'Permits & Leases', href: '#permits' },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full border-b border-white/15 bg-[#0a0a0a]/30 backdrop-blur-md">
      <div className="mx-auto flex w-full items-center justify-between px-5 py-4 sm:px-8 sm:py-5 md:px-12">
        {/* Brand Logo */}
        <Reveal delay={0}>
          <a href="#" className="flex items-center gap-2.5 text-white group">
            <div className="relative flex items-center justify-center">
              <Satellite size={22} strokeWidth={1.5} className="text-white transition-transform duration-300 group-hover:rotate-12" />
              <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-lg sm:text-xl font-medium tracking-tight lowercase">geosign.ai</span>
              <span className="hidden sm:inline-block font-mono text-[9px] uppercase tracking-wider text-white/60 border border-white/15 px-1.5 py-0.5 rounded">
                Gemini 3.5 Flash
              </span>
            </div>
          </a>
        </Reveal>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 lg:gap-10">
          {navLinks.map((link, i) => (
            <Reveal key={link.label} delay={100 + i * 100}>
              <button
                onClick={onLaunchScout}
                className="text-sm text-white/90 hover:text-white transition-colors duration-300 relative inline-flex items-center drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)] cursor-pointer"
              >
                <span>{link.label}</span>
                {link.hasSuper && (
                  <sup className="font-mono text-[10px] text-emerald-400 ml-1 -top-1.5 font-normal">
                    {link.superText}
                  </sup>
                )}
              </button>
            </Reveal>
          ))}
        </nav>

        {/* CTA Button */}
        <Reveal delay={500}>
          <button
            onClick={onLaunchScout}
            className="rounded-md border border-white/20 bg-white/15 backdrop-blur-md px-4 py-2 text-xs sm:px-5 sm:text-sm text-white font-normal hover:bg-white/25 transition-all duration-300 inline-block shadow-sm cursor-pointer"
          >
            Launch Autonomous Scout
          </button>
        </Reveal>
      </div>
    </header>
  );
};
