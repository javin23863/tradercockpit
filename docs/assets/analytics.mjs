import {loadPrelaunchConfig, activatePrelaunch} from '../prelaunch-config.mjs';
try { activatePrelaunch(await loadPrelaunchConfig(new URL('../prelaunch-config.v1.json', import.meta.url))); } catch { document.documentElement.dataset.prelaunch = 'fallback'; }
