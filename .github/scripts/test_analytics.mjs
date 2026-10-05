import assert from 'node:assert/strict';
import {validatePrelaunchConfig} from '../../docs/prelaunch-config.mjs';

const config = {schema:'prelaunch-config/v1', analytics:{provider:'plausible',status:'pending_operator_account',domain:'tradercockpit.app',scriptSrc:''}};
assert.equal(validatePrelaunchConfig(config).analytics.status, 'pending_operator_account', 'Analytics configuration must work without an email-capture service');
for (const scriptSrc of ['http://plausible.io/js/script.js','https://plausible.io.evil.example/script.js','https://evil.example/script.js']) {
  assert.throws(() => validatePrelaunchConfig({...config,analytics:{...config.analytics,status:'active',scriptSrc}}), /HTTPS snippet/);
}
assert.equal(validatePrelaunchConfig({...config,analytics:{...config.analytics,status:'active',scriptSrc:'https://plausible.io/js/script.tagged-events.js'}}).analytics.domain, 'tradercockpit.app');
console.log('ANALYTICS: PASS (independent configuration; HTTPS provider boundary)');
