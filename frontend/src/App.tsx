import { useEffect, useState } from 'react';
import { ScrollVideo } from './components/ScrollVideo';
import { Navbar } from './components/Navbar';
import { SectionOne } from './components/SectionOne';
import { SectionTwo } from './components/SectionTwo';
import { MissionControl } from './components/MissionControl';

export function App() {
  const getInitialView = (): 'landing' | 'scout' => {
    const path = window.location.pathname;
    const hash = window.location.hash;
    if (path === '/scout' || path.startsWith('/scout') || hash === '#scout' || hash === '#mission-control') {
      return 'scout';
    }
    return 'landing';
  };

  const [view, setView] = useState<'landing' | 'scout'>(getInitialView);

  useEffect(() => {
    const handlePopState = () => {
      setView(getInitialView());
    };

    window.addEventListener('popstate', handlePopState);
    window.addEventListener('hashchange', handlePopState);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('hashchange', handlePopState);
    };
  }, []);

  const navigateToScout = () => {
    window.history.pushState({ view: 'scout' }, '', '/scout');
    setView('scout');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const navigateToLanding = () => {
    window.history.pushState({ view: 'landing' }, '', '/');
    setView('landing');
  };

  if (view === 'scout') {
    return <MissionControl onBackToLanding={navigateToLanding} />;
  }

  return (
    <div className="relative min-h-screen bg-[#0a0a0a] text-white selection:bg-emerald-500/30 selection:text-white font-sans antialiased overflow-x-hidden">
      {/* Ultra-smooth Scroll-scrubbed video background */}
      <ScrollVideo />

      {/* Foreground content layer */}
      <div className="relative z-10">
        <Navbar onLaunchScout={navigateToScout} />
        <main>
          <SectionOne onLaunchScout={navigateToScout} />
          {/* Spacer div h-[80vh] (aria-hidden) critical for scroll video scrub length */}
          <div className="h-[80vh]" aria-hidden="true" />
          <SectionTwo onLaunchScout={navigateToScout} />
        </main>
      </div>
    </div>
  );
}

export default App;
