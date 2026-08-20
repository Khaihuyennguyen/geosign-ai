import { useEffect, useRef, useState } from 'react';

const VIDEO_URL = 'https://d8j0ntlcm91z4.cloudfront.net/user_30iO0yg9MnGGbCaKvr8SNXnoBMT/hf_20260820_080755_ec8de128-4281-4e29-b096-fc98555fff52.mp4';
const LOCAL_VIDEO_URL = '/hero.mp4';
const POSTER_URL = 'https://cdn.higgsfield.ai/user_30iO0yg9MnGGbCaKvr8SNXnoBMT/hf_20260820_080755_ec8de128-4281-4e29-b096-fc98555fff52_thumbnail.webp';
const LOCAL_POSTER_URL = '/hero-poster.jpg';

export const ScrollVideo = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [canvasReady, setCanvasReady] = useState(false);
  const [posterLoaded, setPosterLoaded] = useState(false);

  const framesRef = useRef<ImageBitmap[]>([]);
  const targetProgressRef = useRef(0);
  const smoothedProgressRef = useRef(0);
  const lastRenderedIndexRef = useRef<number>(-1);
  const rafIdRef = useRef<number>(0);

  // Resize canvas according to DPR
  const updateCanvasDimensions = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(window.innerWidth * dpr);
    canvas.height = Math.round(window.innerHeight * dpr);
    lastRenderedIndexRef.current = -1;
  };

  // Draw object-cover
  const drawFrame = (image: ImageBitmap | HTMLVideoElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false, desynchronized: true });
    if (!ctx) return;

    const cw = canvas.width;
    const ch = canvas.height;
    const iw = image instanceof ImageBitmap ? image.width : image.videoWidth;
    const ih = image instanceof ImageBitmap ? image.height : image.videoHeight;
    if (!iw || !ih) return;

    const scale = Math.max(cw / iw, ch / ih);
    const dw = Math.ceil(iw * scale);
    const dh = Math.ceil(ih * scale);
    const dx = Math.floor((cw - dw) / 2);
    const dy = Math.floor((ch - dh) / 2);

    ctx.drawImage(image, dx, dy, dw, dh);
  };

  // Animation and Scroll Tracking Loop
  useEffect(() => {
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (scrollHeight > 0) {
        targetProgressRef.current = Math.min(1, Math.max(0, window.scrollY / scrollHeight));
      } else {
        targetProgressRef.current = 0;
      }
    };

    const handleResize = () => {
      updateCanvasDimensions();
      handleScroll();
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleResize);
    updateCanvasDimensions();
    handleScroll();

    let lastTime = performance.now();

    const loop = (time: number) => {
      const delta = Math.min(64, time - lastTime);
      lastTime = time;

      const factor = 1 - Math.pow(1 - 0.14, delta / 16.67);
      smoothedProgressRef.current += (targetProgressRef.current - smoothedProgressRef.current) * factor;
      const smoothed = smoothedProgressRef.current;

      const frames = framesRef.current;
      if (frames.length > 0) {
        const frameIndex = Math.min(
          frames.length - 1,
          Math.max(0, Math.round(smoothed * (frames.length - 1)))
        );

        if (frameIndex !== lastRenderedIndexRef.current) {
          const frame = frames[frameIndex];
          if (frame) {
            drawFrame(frame);
            lastRenderedIndexRef.current = frameIndex;
          }
        }
      } else {
        const video = videoRef.current;
        if (video && video.duration && !video.seeking) {
          const targetTime = smoothed * Math.max(0, video.duration - 0.05);
          if (Math.abs(video.currentTime - targetTime) > 0.03) {
            video.currentTime = targetTime;
          }
        }
      }

      rafIdRef.current = requestAnimationFrame(loop);
    };

    rafIdRef.current = requestAnimationFrame(loop);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  // Progressive Frame Cache Extractor
  useEffect(() => {
    let isCancelled = false;

    const extractFrames = async () => {
      try {
        const offscreen = document.createElement('video');
        offscreen.crossOrigin = 'anonymous';
        offscreen.muted = true;
        offscreen.playsInline = true;
        offscreen.preload = 'auto';
        offscreen.src = LOCAL_VIDEO_URL;

        offscreen.onerror = () => {
          if (!isCancelled) offscreen.src = VIDEO_URL;
        };

        await new Promise<void>((resolve, reject) => {
          offscreen.onloadedmetadata = () => resolve();
          offscreen.onerror = () => reject(new Error('Failed to load video metadata'));
        });

        if (isCancelled) return;

        const duration = offscreen.duration || 5;
        const vw = offscreen.videoWidth || 1920;
        const vh = offscreen.videoHeight || 1080;
        const targetWidth = Math.min(960, vw);
        const targetHeight = Math.round(targetWidth * (vh / vw));

        const offscreenCanvas = document.createElement('canvas');
        offscreenCanvas.width = targetWidth;
        offscreenCanvas.height = targetHeight;
        const offCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true });
        if (!offCtx) return;

        // Phase 1: Fast Pass (30 frames)
        const fastFramesCount = 30;
        const fastFrames: ImageBitmap[] = [];

        for (let i = 0; i < fastFramesCount; i++) {
          if (isCancelled) return;
          const time = (i / (fastFramesCount - 1)) * Math.max(0, duration - 0.05);

          await new Promise<void>((resolve) => {
            const onSeeked = () => {
              offscreen.removeEventListener('seeked', onSeeked);
              resolve();
            };
            offscreen.addEventListener('seeked', onSeeked);
            offscreen.currentTime = time;
          });

          if (isCancelled) return;
          offCtx.drawImage(offscreen, 0, 0, targetWidth, targetHeight);
          const bitmap = await createImageBitmap(offscreenCanvas);
          fastFrames.push(bitmap);
        }

        if (!isCancelled && fastFrames.length > 0) {
          framesRef.current = fastFrames;
          setCanvasReady(true);
          lastRenderedIndexRef.current = -1;
        }

        // Phase 2: High-Density Pass (84 frames)
        const fullFramesCount = Math.min(84, Math.max(48, Math.round(duration * 12)));
        const fullFrames: ImageBitmap[] = [];

        for (let i = 0; i < fullFramesCount; i++) {
          if (isCancelled) return;
          const time = (i / (fullFramesCount - 1)) * Math.max(0, duration - 0.05);

          await new Promise<void>((resolve) => {
            const onSeeked = () => {
              offscreen.removeEventListener('seeked', onSeeked);
              resolve();
            };
            offscreen.addEventListener('seeked', onSeeked);
            offscreen.currentTime = time;
          });

          if (isCancelled) return;
          offCtx.drawImage(offscreen, 0, 0, targetWidth, targetHeight);
          const bitmap = await createImageBitmap(offscreenCanvas);
          fullFrames.push(bitmap);
        }

        if (!isCancelled && fullFrames.length >= fullFramesCount) {
          const oldFrames = framesRef.current;
          framesRef.current = fullFrames;
          lastRenderedIndexRef.current = -1;
          oldFrames.forEach((b) => b.close?.());
        }
      } catch (err) {
        console.warn('Frame cache extraction notice:', err);
      }
    };

    const video = videoRef.current;
    if (video) {
      if (video.readyState >= 2) {
        setVideoLoaded(true);
        extractFrames();
      } else {
        video.addEventListener('loadeddata', () => {
          setVideoLoaded(true);
          extractFrames();
        }, { once: true });
      }
    }

    return () => {
      isCancelled = true;
      framesRef.current.forEach((bitmap) => bitmap.close?.());
      framesRef.current = [];
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 bg-[#0a0a0a] overflow-hidden pointer-events-none select-none">
      {/* 1. Poster image layer */}
      <img
        src={LOCAL_POSTER_URL}
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).src = POSTER_URL;
        }}
        onLoad={() => setPosterLoaded(true)}
        alt="GeoSignAI Autonomous Geospatial Background"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 will-change-[opacity] ${
          canvasReady || videoLoaded ? 'opacity-0' : posterLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* 2. Video fallback layer */}
      <video
        ref={videoRef}
        muted
        playsInline
        preload="auto"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-500 will-change-[opacity] ${
          videoLoaded && !canvasReady ? 'opacity-100' : 'opacity-0'
        }`}
        onError={(e) => {
          const v = e.currentTarget as HTMLVideoElement;
          if (v.src.endsWith('hero.mp4')) {
            v.src = VIDEO_URL;
          }
        }}
      >
        <source src={LOCAL_VIDEO_URL} type="video/mp4" />
        <source src={VIDEO_URL} type="video/mp4" />
      </video>

      {/* 3. Scrubbed Canvas layer */}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 w-full h-full block transition-opacity duration-500 will-change-transform ${
          canvasReady ? 'opacity-100' : 'opacity-0'
        }`}
        style={{ transform: 'translateZ(0)' }}
      />

      {/* 4. Very subtle, light ambient gradient to keep video bright while preserving text legibility */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/50 pointer-events-none" />
    </div>
  );
};
