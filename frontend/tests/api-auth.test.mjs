import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const source = readFileSync(new URL('../src/lib/api.js', import.meta.url), 'utf8');
function client(responses, prod = true) {
  const calls = [], events = [];
  const context = vm.createContext({
    env: { PROD: prod, VITE_API_BASE_URL: 'https://backend.example' },
    window: { location: { origin: 'https://frontend.example' }, dispatchEvent: e => events.push(e.type) },
    FormData, Event, CustomEvent, AbortSignal,
    setTimeout: callback => callback(),
    fetch: async (url, options) => {
      calls.push({ url, options });
      const result = responses.shift();
      if (result instanceof Error) throw result;
      assert.ok(result, `Unexpected request: ${url}`);
      const [status, body] = result;
      return { ok: status >= 200 && status < 300, status, json: async () => body };
    },
  });
  vm.runInContext(source.replaceAll('import.meta.env', 'env').replaceAll('export ', '') + '\nglobalThis.api = api;', context);
  return { api: context.api, calls, events };
}

test('production ignores cross-site API override and verifies cookie after login', async () => {
  const c = client([[200, { name: 'Admin' }], [200, { name: 'Admin', mode: 'ONLINE' }]]);
  assert.equal((await c.api.login('admin', 'test')).mode, 'ONLINE');
  assert.deepEqual(c.calls.map(x => x.url), ['https://frontend.example/api/auth/login', 'https://frontend.example/api/auth/session']);
  assert.ok(c.calls.every(x => x.options.credentials === 'include' && x.options.cache === 'no-store'));
});
test('development retains explicit local API configuration', async () => {
  const c = client([[200, []]], false);
  await c.api.listTenders();
  assert.equal(c.calls[0].url, 'https://backend.example/api/tenders');
});
test('login cannot display authenticated dashboard without a retained cookie', async () => {
  const c = client([[200, {}], [401, { detail: 'Sign in' }]]);
  await assert.rejects(c.api.login('admin', 'test'), /cookie was not retained/);
  assert.deepEqual(c.events, []);
});
test('job 401 does not discard a valid session or retry the POST', async () => {
  const c = client([[401, { detail: 'Job permission denied' }], [200, { mode: 'ONLINE' }]]);
  await assert.rejects(c.api.extractTender(3), /Job permission denied/);
  assert.deepEqual(c.events, []);
  assert.equal(c.calls.filter(x => x.options.method === 'POST').length, 1);
});
test('confirmed expired session requests sign-in', async () => {
  const c = client([[401, { detail: 'Sign in' }], [401, {}]]);
  await assert.rejects(c.api.extractTender(3));
  assert.deepEqual(c.events, ['bidlens:unauthenticated']);
});
test('failed session probe preserves workspace and reports original error', async () => {
  const c = client([[401, { detail: 'Cannot start job' }], new Error('offline')]);
  await assert.rejects(c.api.extractTender(3), /Cannot start job/);
  assert.deepEqual(c.events, []);
});
test('creation and polling share the authenticated origin through completion', async () => {
  const c = client([[202, { job_id: 'job' }], [200, { status: 'RUNNING' }], [200, { status: 'COMPLETED', result: { requirements: 2 } }]]);
  assert.equal((await c.api.extractTender(3)).requirements, 2);
  assert.ok(c.calls.every(x => x.url.startsWith('https://frontend.example/api/jobs/') && x.options.credentials === 'include'));
});
test('polling failure with valid session does not log out', async () => {
  const c = client([[202, { job_id: 'job' }], [401, { detail: 'Polling unavailable' }], [200, {}]]);
  await assert.rejects(c.api.extractTender(3), /Polling unavailable/);
  assert.deepEqual(c.events, []);
});
test('startup session check is non-destructive and preserves status for caller', async () => {
  const c = client([[503, { detail: 'Server unavailable' }]]);
  await assert.rejects(c.api.session(), e => e.status === 503);
  assert.ok(!c.events.includes('bidlens:unauthenticated'));
});
