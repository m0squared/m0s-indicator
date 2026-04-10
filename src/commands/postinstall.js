'use strict';

// Runs automatically after: npm install -g m0squared-indicator
// Skipped for local project installs (npm_config_global is not set)
if (process.env.npm_config_global) {
  require('./install')().catch(err => {
    console.error('\n  M0² auto-install failed:', err.message);
    console.error('  Run "m0squared-indicator install" manually.\n');
  });
}
