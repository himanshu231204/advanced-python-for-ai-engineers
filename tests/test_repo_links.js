const test = require('node:test');
const assert = require('node:assert/strict');
const links = require('../docs/assets/repo-links.js');
const docs = {
  parent: {source: '00-foundation/README.md'},
  child: {source: '00-foundation/child.md'},
  sibling: {source: '00-foundation/sibling.md'},
  other: {source: '01-functions/README.md'},
  interview: {source: 'INTERVIEW.md'},
  debug: {source: 'debugging/exercises/broken'},
};
const repo = 'https://github.com/example/repo';
const resolve = (href, id = 'parent') => links.resolveLink(href, id, docs, repo);
test('source-relative lesson, sibling, parent and directory links', () => {
  assert.equal(resolve('child.md#hello'), '#/child#hello');
  assert.equal(resolve('./sibling.md', 'child'), '#/sibling');
  assert.equal(resolve('README.md', 'child'), '#/parent');
  assert.equal(resolve('../01-functions/'), '#/other');
  assert.equal(resolve('../01-functions/README.md#hello'), '#/other#hello');
  assert.equal(resolve('/INTERVIEW.md'), '#/interview');
  assert.equal(resolve('../README.md'), '#/home');
  assert.equal(resolve('README.md', 'debug'), '#/debug');
  assert.equal(resolve('../fixed.py', 'debug'), repo + '/blob/main/debugging/exercises/fixed.py');
});
test('fragments and encoded route IDs survive reload parsing', () => {
  assert.equal(resolve('#13--interview-questions'), '#/parent#13--interview-questions');
  assert.deepEqual(links.parseRoute('#/a%2Fb#hello%20world'), {id: 'a/b', fragment: 'hello world'});
  assert.deepEqual(links.parseRoute(''), {id: 'home', fragment: ''});
  assert.equal(links.normalizeHeading('13--interview-questions'), '13-interview-questions');
});
test('external links remain external and unsafe schemes cannot become local pages', () => {
  assert.equal(resolve('https://example.com/a#b'), 'https://example.com/a#b');
  assert.equal(resolve('//example.com/a'), '//example.com/a');
  assert.equal(resolve('javascript:alert(1)'), null);
  assert.equal(resolve('data:text/html,hi'), null);
  assert.equal(resolve('../AGENTS.md#rules'), repo + '/blob/main/AGENTS.md#rules');
});
