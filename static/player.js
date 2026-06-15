(() => {
  const frame = document.querySelector("[data-video-frame]");
  const video = document.querySelector("[data-watch-video]");
  const fullscreenButton = document.querySelector("[data-fullscreen-landscape]");

  if (!frame || !video || !fullscreenButton) {
    return;
  }

  const lockLandscape = async () => {
    if (!screen.orientation || !screen.orientation.lock) {
      return;
    }

    try {
      await screen.orientation.lock("landscape");
    } catch (_error) {
      // Some browsers only allow orientation lock in fullscreen, and iOS ignores it.
    }
  };

  const unlockOrientation = () => {
    if (!screen.orientation || !screen.orientation.unlock) {
      return;
    }

    try {
      screen.orientation.unlock();
    } catch (_error) {
      // Ignore unsupported browser behavior.
    }
  };

  const enterFullscreen = async () => {
    try {
      if (frame.requestFullscreen) {
        await frame.requestFullscreen();
        await lockLandscape();
        return;
      }

      if (video.requestFullscreen) {
        await video.requestFullscreen();
        await lockLandscape();
        return;
      }
    } catch (_error) {
      // Fall through to the iOS-specific native video fullscreen path below.
    }

    if (video.webkitEnterFullscreen) {
      try {
        video.webkitEnterFullscreen();
      } catch (_error) {
        // Ignore unsupported browser behavior.
      }
    }
  };

  fullscreenButton.addEventListener("click", enterFullscreen);

  document.addEventListener("fullscreenchange", () => {
    if (document.fullscreenElement) {
      lockLandscape();
    } else {
      unlockOrientation();
    }
  });
})();
