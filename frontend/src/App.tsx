import { useState } from 'react';
import { ScrollVideo } from './components/ScrollVideo';
import { Navbar } from './components/Navbar';
import { SectionOne } from './components/SectionOne';
import { SectionTwo } from './components/SectionTwo';
import { MissionControl } from './components/MissionControl';

export function App() {
  const [view, setView] = useState<'landing' | 'scout'>('landing');

  if (view === 'scout') {
    return <MissionControl onBackToLanding={() => setView('landing')} />;
  }

  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white selection:bg-emerald-500/30 selection:text-white font-sans antialiased overflow-x-hidden">
      {/* Ultra-smooth Scroll-scrubbed video background */}
      <ScrollVideo />

      {/* Foreground content layer */}
      <div className="relative z-10">
        <Navbar onLaunchScout={() => setView('scout')} />
        <main>
          <SectionOne onLaunchScout={() => setView('scout')} />
          {/* Spacer div h-[80vh] (aria-hidden) critical for scroll video scrub length */}
          <div className="h-[80vh]" aria-hidden="true" />
          <SectionTwo onLaunchScout={() => setView('scout')} />
        </main>
      </div>
    </div>
  );
}

export default App;
