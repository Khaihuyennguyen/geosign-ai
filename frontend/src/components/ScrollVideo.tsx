import { useEffect, useRef, useState } from 'react';

const LOCAL_VIDEO_URL = '/hero.mp4';
const REMOTE_VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_30iO0yg9MnGGbCaKvr8SNXnoBMT/hf_20260820_080755_ec8de128-4281-4e29-b096-fc98555fff52.mp4';
const LOCAL_POSTER_URL = '/hero-poster.jpg';
const REMOTE_POSTER_URL =
  'https://cdn.higgsfield.ai/user_30iO0yg9MnGGbCaKvr8SNXnoBMT/hf_20260820_080755_ec8de128-4281-4e29-b096-fc98555fff52_thumbnail.webp';

export const ScrollVideo = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [posterLoaded, setPosterLoaded] = useState(false);

  const framesRef = useRef<ImageBitmap[]>([]);
  const targetProgressRef = useRef(0);
  const smoothedProgressRef = useRef(0);
  const rafIdRef = useRef<number>(0);
  const isSeekingRef = useRef(false);

  // Resize canvas according to DPR
  const updateCanvasDimensions = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(window.innerWidth * dpr);
    canvas.height = Math.round(window.innerHeight * dpr);
  };

  // Draw object-cover to canvas
  const drawFrame = (image: ImageBitmap | HTMLVideoElement) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: false });
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

  // Main scroll animation loop
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
      const delta = Math.min(50, time - lastTime);
      lastTime = time;

      // Smooth lerp (responsive ~0.16)
      const factor = 1 - Math.pow(1 - 0.16, delta / 16.67);
      smoothedProgressRef.current += (targetProgressRef.current - smoothedProgressRef.current) * factor;
      const smoothed = smoothedProgressRef.current;

      const frames = framesRef.current;
      if (frames.length > 0) {
        const frameIndex = Math.min(
          frames.length - 1,
          Math.max(0, Math.round(smoothed * (frames.length - 1)))
        );
        const frame = frames[frameIndex];
        if (frame) {
          drawFrame(frame);
        }
      } else {
        // Direct video sync before frame cache finishes
        const video = videoRef.current;
        if (video && video.duration && !isSeekingRef.current) {
          const targetTime = smoothed * Math.max(0, video.duration - 0.05);
          if (Math.abs(video.currentTime - targetTime) > 0.03) {
            isSeekingRef.current = true;
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

  // Sync visible video seeking
  const onVideoSeeked = () => {
    isSeekingRef.current = false;
    const video = videoRef.current;
    if (video && framesRef.current.length === 0) {
      drawFrame(video);
    }
  };

  // Pre-decode frames in background for 60-120fps scrubbing
  useEffect(() => {
    let isCancelled = false;

    const extractFrames = async () => {
      try {
        const offscreen = document.createElement('video');
        offscreen.muted = true;
        offscreen.playsInline = true;
        offscreen.preload = 'auto';
        offscreen.crossOrigin = 'anonymous';
        offscreen.src = LOCAL_VIDEO_URL;

        offscreen.onerror = () => {
          if (!isCancelled) offscreen.src = REMOTE_VIDEO_URL;
        };

        await new Promise<void>((resolve, reject) => {
          offscreen.onloadedmetadata = () => resolve();
          offscreen.onerror = () => reject(new Error('Failed to load video'));
        });

        if (isCancelled) return;

        const duration = offscreen.duration || 5;
        const totalFrames = 48; // Optimal balance between extraction speed and silky motion
        const vw = offscreen.videoWidth || 1280;
        const vh = offscreen.videoHeight || 720;
        const targetWidth = Math.min(960, vw);
        const targetHeight = Math.round(targetWidth * (vh / vw));

        const offCanvas = document.createElement('canvas');
        offCanvas.width = targetWidth;
        offCanvas.height = targetHeight;
        const offCtx = offCanvas.getContext('2d', { willReadFrequently: true });
        if (!offCtx) return;

        const extracted: ImageBitmap[] = [];

        for (let i = 0; i < totalFrames; i++) {
          if (isCancelled) return;
          const time = (i / (totalFrames - 1)) * Math.max(0, duration - 0.05);

          await new Promise<void>((resolve) => {
            const onSeek = () => {
              offscreen.removeEventListener('seeked', onSeek);
              resolve();
            };
            offscreen.addEventListener('seeked', onSeek);
            offscreen.currentTime = time;
          });

          if (isCancelled) return;
          offCtx.drawImage(offscreen, 0, 0, targetWidth, targetHeight);
          const bitmap = await createImageBitmap(offCanvas);
          extracted.push(bitmap);

          // Update buffer progressively so scrubbing starts immediately
          if (extracted.length === 12 || extracted.length === 24 || extracted.length === totalFrames) {
            framesRef.current = [...extracted];
          }
        }

        if (!isCancelled && extracted.length > 0) {
          framesRef.current = extracted;
        }
      } catch (err) {
        console.warn('Frame cache notice (using native video stream):', err);
      }
    };

    const video = videoRef.current;
    if (video) {
      if (video.readyState >= 2) {
        setVideoLoaded(true);
        extractFrames();
      } else {
        video.addEventListener(
          'loadeddata',
          () => {
            setVideoLoaded(true);
            extractFrames();
          },
          { once: true }
        );
      }
    }

    return () => {
      isCancelled = true;
      framesRef.current.forEach((b) => b.close?.());
      framesRef.current = [];
    };
  }, []);

  return (
    <div className="fixed inset-0 z-0 bg-[#0a0a0a] overflow-hidden pointer-events-none select-none">
      {/* 1. Poster fallback */}
      <img
        src={LOCAL_POSTER_URL}
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).src = REMOTE_POSTER_URL;
        }}
        onLoad={() => setPosterLoaded(true)}
        alt="GeoSignAI Background"
        className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ${
          videoLoaded ? 'opacity-0' : posterLoaded ? 'opacity-100' : 'opacity-0'
        }`}
      />

      {/* 2. Background Video */}
      <video
        ref={videoRef}
        muted
        playsInline
        preload="auto"
        onSeeked={onVideoSeeked}
        onLoadedData={() => {
          setVideoLoaded(true);
          const v = videoRef.current;
          if (v) drawFrame(v);
        }}
        className="absolute inset-0 w-full h-full object-cover opacity-0 pointer-events-none"
        onError={(e) => {
          const v = e.currentTarget as HTMLVideoElement;
          if (v.src.endsWith('hero.mp4')) {
            v.src = REMOTE_VIDEO_URL;
          }
        }}
      >
        <source src={LOCAL_VIDEO_URL} type="video/mp4" />
        <source src={REMOTE_VIDEO_URL} type="video/mp4" />
      </video>

      {/* 3. Scrubbed Canvas Layer */}
      <canvas
        ref={canvasRef}
        className={`absolute inset-0 w-full h-full block transition-opacity duration-500 ${
          videoLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        style={{ transform: 'translateZ(0)' }}
      />

      {/* 4. Subtle contrast ambient lighting */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/50 pointer-events-none" />
    </div>
  );
};
