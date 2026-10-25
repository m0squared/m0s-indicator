'use strict';

// Runs automatically after: npm install -g m0squared-indicator
// Skipped for local project installs (npm_config_global is not set)
if (process.env.npm_config_global) {
  const python = require('../python');
  if (!python.findPython().argv) {
    // Fail the global install outright: without Python the HUD cannot run,
    // and a half-installed tool is worse than a clear error.
    console.error('\n  M0² Indicator cannot be installed:');
    for (const line of python.requirementMessage()) console.error('  ' + line);
    console.error();
    process.exit(1);
  }
  require('./install')().catch(err => {
    console.error('\n  M0² auto-install failed:', err.message);
    console.error('  Run "m0squared-indicator install" manually.\n');
    process.exit(1);
  });
}
