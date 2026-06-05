import React from 'react';
import { videoUrl } from '../constants/appConstants';

export function BackgroundVideo() {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);

  React.useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;

    let frame = 0;
    const edgeBuffer = 0.18;

    const tick = () => {
      const duration = video.duration;

      if (Number.isFinite(duration) && duration > 0) {
        if (video.currentTime >= duration - edgeBuffer) {
          video.currentTime = duration - edgeBuffer;
          video.pause();
          return;
        }
      }

      frame = window.requestAnimationFrame(tick);
    };

    void video.play();
    frame = window.requestAnimationFrame(tick);

    return () => window.cancelAnimationFrame(frame);
  }, []);

  return <video ref={videoRef} className="absolute inset-0 h-full w-full object-cover" src={videoUrl} autoPlay muted playsInline />;
}
