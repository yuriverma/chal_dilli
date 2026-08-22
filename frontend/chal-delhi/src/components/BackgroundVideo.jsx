import React, { useEffect, useState } from "react";
import bgVideo from "../assets/bg2.MP4";
import bgPoster from "../assets/bg-poster.jpg";

/**
 * The full-screen ambient background, shared by every page.
 *
 * There is a poster image and a solid ground underneath the video, and they are
 * not decoration. The source video used to be HEVC in a QuickTime container
 * (renamed to .MP4), which Safari played and Chrome did not. With nothing
 * behind it, a browser that could not decode the video fell through to the
 * white default canvas — and since the panels on top are translucent and the
 * heading text is dark, the entire page read as broken. Painting a correct
 * ground first means a video that fails to decode, is still downloading, or is
 * deliberately skipped degrades to "looks right, just static".
 *
 * The video is skipped entirely on small screens: it is 6MB of decoration and
 * mobile visitors pay for it. It is also skipped for anyone who has asked for
 * reduced motion.
 */

// Matches Tailwind's `md` breakpoint, which is where the layouts switch to
// their wide arrangement anyway.
const WIDE_SCREEN = "(min-width: 768px)";
const REDUCED_MOTION = "(prefers-reduced-motion: reduce)";

const shouldPlayVideo = () => {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  return (
    window.matchMedia(WIDE_SCREEN).matches &&
    !window.matchMedia(REDUCED_MOTION).matches
  );
};

const BackgroundVideo = () => {
  const [playVideo, setPlayVideo] = useState(shouldPlayVideo);
  // Until the video reports a real frame, the poster stays on top. videoWidth
  // is the honest signal here: a browser that cannot decode the track still
  // reports readyState 4 and paused false, but leaves videoWidth at 0.
  const [videoReady, setVideoReady] = useState(false);

  useEffect(() => {
    if (!window.matchMedia) return;
    const wide = window.matchMedia(WIDE_SCREEN);
    const onChange = () => setPlayVideo(shouldPlayVideo());
    wide.addEventListener("change", onChange);
    return () => wide.removeEventListener("change", onChange);
  }, []);

  const confirmDecoded = (event) => {
    if (event.currentTarget.videoWidth > 0) setVideoReady(true);
  };

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 -z-10 overflow-hidden bg-[#12213d]"
      style={{
        backgroundImage: `url(${bgPoster})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {playVideo && (
        <video
          src={bgVideo}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          poster={bgPoster}
          onLoadedData={confirmDecoded}
          onCanPlay={confirmDecoded}
          className={`h-full w-full object-cover transition-opacity duration-700 ${
            videoReady ? "opacity-100" : "opacity-0"
          }`}
        />
      )}
    </div>
  );
};

export default BackgroundVideo;
