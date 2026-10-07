// Run from the skill folder: node --test tests/*.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(here, '..', 'scripts', 'writing-gate-hook.mjs');
const FAKE_CHECKER = join(here, 'fixtures', 'fake-checker.mjs');

// A throwaway skill folder with one voice named "demo".
const SKILL = mkdtempSync(join(tmpdir(), 'wlm-hook-'));
mkdirSync(join(SKILL, 'voices', 'demo'), { recursive: true });
writeFileSync(join(SKILL, 'voices', 'demo', 'profile.json'), '{}');
writeFileSync(join(SKILL, 'voices', 'demo', 'hook.json'), JSON.stringify({
  defaultRegister: 'essay',
  registers: { letter: ['/letters/', 'cover'] },
  addInclude: ['field-notes'],
  promptPhrases: ['tidy this up'],
}));

const FAKE_ENV = {
  WRITE_LIKE_ME_PYTHON: process.execPath,
  WRITE_LIKE_ME_CHECKER: FAKE_CHECKER,
  WRITE_LIKE_ME_SKILL_DIR: SKILL,
  WRITE_LIKE_ME_VOICE: 'demo',
  WRITE_LIKE_ME_PROFILE: '',
};

function run(mode, stdin, env = FAKE_ENV, extraArgs = []) {
  const res = spawnSync(process.execPath, [SCRIPT, mode, ...extraArgs], {
    input: stdin,
    encoding: 'utf8',
    env: { ...process.env, ...env },
  });
  return { status: res.status, stdout: res.stdout, stderr: res.stderr };
}

function write(filePath, tool = 'Write', env = FAKE_ENV, extraArgs = []) {
  return run('post-write', JSON.stringify({ tool_name: tool, tool_input: { file_path: filePath } }), env, extraArgs);
}

const json = (r) => JSON.parse(r.stdout.trim());

// ----- post-write: reader text detection -----

test('a path with a writing marker is a reader text and uses the default register from hook.json', () => {
  const r = write('D:\\work\\writing\\essay-block.md');
  assert.equal(r.status, 0);
  assert.match(json(r).reason, /register=essay/);
});

test('hook.json registers map a path marker to a register', () => {
  const r = write('D:\\work\\writing\\cover-block.md');
  assert.match(json(r).reason, /register=letter/);
});

test('forward slashes work', () => {
  const r = write('D:/work/letters/note-block.md');
  assert.match(json(r).reason, /register=letter/);
});

test('addInclude extends the default markers', () => {
  const r = write('D:\\work\\field-notes\\day-block.md');
  assert.equal(json(r).decision, 'block');
});

test('evidence and input folders are excluded', () => {
  for (const dir of ['snapshots', 'extracted', 'transcripts', 'corpus', 'fixtures', 'evidence']) {
    assert.equal(write(`D:\\work\\writing\\${dir}\\essay-block.md`).stdout, '', dir);
  }
});

test('the skill voices folder is excluded', () => {
  assert.equal(write('D:\\skills\\write-like-me\\voices\\demo\\writing-block.md').stdout, '');
});

test('README.md under a writing folder is not a reader text', () => {
  assert.equal(write('D:\\work\\writing\\README.md').stdout, '');
});

test('plan- prefixed file is not a reader text', () => {
  assert.equal(write('D:\\work\\writing\\plan-site.md').stdout, '');
});

test('.py file is not a reader text', () => {
  assert.equal(write('D:\\work\\writing\\tool.py').stdout, '');
});

test('path without a reader marker is not a reader text', () => {
  assert.equal(write('D:\\work\\misc\\notes.md').stdout, '');
});

test('tool_input.path and toolInput fallbacks are accepted', () => {
  const a = run('post-write', JSON.stringify({ tool_input: { path: 'D:\\x\\writing\\a-review.md' } }));
  assert.match(json(a).hookSpecificOutput.additionalContext, /VOICE_CHECK_REVIEW/);
  const b = run('post-write', JSON.stringify({ toolInput: { filePath: 'D:\\x\\writing\\a-review.txt' } }));
  assert.match(json(b).hookSpecificOutput.additionalContext, /VOICE_CHECK_REVIEW/);
});

// ----- voice selection -----

test('the profile of the chosen voice is passed to the checker', () => {
  const r = write('D:\\work\\writing\\essay-block.md', 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_VOICE: '' }, ['--voice', 'demo']);
  assert.match(json(r).reason, /profile=profile\.json/);
});

test('a single voice in voices/ is used when none is named', () => {
  const r = write('D:\\work\\writing\\essay-block.md', 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_VOICE: '' });
  assert.match(json(r).reason, /profile=profile\.json/);
});

test('without a voice or a profile file the checker runs the universal baseline', () => {
  const empty = mkdtempSync(join(tmpdir(), 'wlm-empty-'));
  const r = write('D:\\work\\writing\\essay-block.md', 'Write', {
    ...FAKE_ENV, WRITE_LIKE_ME_VOICE: '', WRITE_LIKE_ME_SKILL_DIR: empty,
  });
  assert.match(json(r).reason, /profile=none/);
  assert.match(json(r).reason, /register=none/);
});

// ----- post-write: checker outcomes -----

test('BLOCK verdict returns decision block with reason and system message', () => {
  const o = json(write('D:\\work\\writing\\essay-block.md', 'Edit'));
  assert.equal(o.decision, 'block');
  assert.match(o.reason, /^write-like-me checker: VOICE_CHECK_BLOCK on D:\\work/);
  assert.match(o.reason, /Fix every block hit, then write the file again\./);
  assert.match(o.reason, /em-dash: a dash here/);
  assert.match(o.reason, /tricolon: fast, clear, and good/);
  assert.doesNotMatch(o.reason, /hedge/);
  assert.equal(o.systemMessage, 'write-like-me: BLOCK on essay-block.md (2 block hits)');
});

test('REVIEW verdict returns additionalContext', () => {
  const o = json(write('D:\\work\\writing\\essay-review.md', 'MultiEdit'));
  assert.equal(o.hookSpecificOutput.hookEventName, 'PostToolUse');
  assert.match(o.hookSpecificOutput.additionalContext, /VOICE_CHECK_REVIEW on .*essay-review\.md/);
  assert.match(o.hookSpecificOutput.additionalContext, /Resolve or justify each review hit in one line/);
  assert.equal(o.systemMessage, 'write-like-me: REVIEW on essay-review.md (1 review hits)');
});

test('PASS verdict returns only a system message', () => {
  assert.deepEqual(json(write('D:\\work\\writing\\essay-fine.md')), { systemMessage: 'write-like-me: PASS on essay-fine.md' });
});

test('final token is used when the JSON does not parse', () => {
  assert.match(json(write('D:\\work\\writing\\essay-plain.md')).hookSpecificOutput.additionalContext, /VOICE_CHECK_REVIEW/);
});

test('missing checker path gives the could-not-run output', () => {
  const r = write('D:\\work\\writing\\essay.md', 'Write', {
    ...FAKE_ENV, WRITE_LIKE_ME_CHECKER: join(here, 'fixtures', 'does-not-exist.mjs'),
  });
  assert.equal(r.status, 0);
  const o = json(r);
  assert.match(o.hookSpecificOutput.additionalContext, /write-like-me checker could not run on .*essay\.md: /);
  assert.match(o.hookSpecificOutput.additionalContext, /Run it by hand before showing the text\./);
  assert.equal(o.decision, undefined);
});

test('missing python executable gives the could-not-run output', () => {
  const r = write('D:\\work\\writing\\essay.md', 'Write', {
    ...FAKE_ENV, WRITE_LIKE_ME_PYTHON: 'definitely-not-a-real-python-binary',
  });
  assert.equal(r.status, 0);
  assert.match(json(r).hookSpecificOutput.additionalContext, /could not run/);
});

test('checker crash without parsable output gives the could-not-run output', () => {
  assert.match(json(write('D:\\work\\writing\\essay-crash.md')).hookSpecificOutput.additionalContext, /could not run/);
});

test('output is exactly one JSON line', () => {
  const r = write('D:\\work\\writing\\essay-block.md');
  assert.equal(r.stdout.trim().split('\n').length, 1);
  assert.equal(r.stderr, '');
});

// ----- prompt mode -----

const promptRun = (prompt) => run('prompt', JSON.stringify({ prompt }));

test('prompt: request verb near reader noun matches', () => {
  const r = promptRun('Can you write a reply to this email?');
  assert.equal(r.status, 0);
  const o = json(r);
  assert.equal(o.hookSpecificOutput.hookEventName, 'UserPromptSubmit');
  assert.match(o.hookSpecificOutput.additionalContext, /write-like-me applies now/);
  assert.match(o.hookSpecificOutput.additionalContext, /09-how-to-write\.md/);
});

test('prompt: trigger phrase matches', () => {
  assert.notEqual(promptRun('how does this come across?').stdout, '');
  assert.notEqual(promptRun('Is this GOOD enough to send').stdout, '');
});

test('prompt: phrases from hook.json match', () => {
  assert.notEqual(promptRun('please tidy this up before Friday').stdout, '');
});

test('prompt: unrelated prompts do not match', () => {
  assert.equal(promptRun('run the tests again').stdout, '');
  assert.equal(promptRun('fix the bug in parser.py').stdout, '');
});

test('prompt: too short does not match', () => {
  assert.equal(promptRun('grammar').stdout, '');
});

test('prompt: pasted code block does not match', () => {
  const code = '```js\nfunction write() {\n  return sendEmail(message);\n}\n```';
  assert.equal(promptRun(code).stdout, '');
});

test('prompt: path-heavy prompt does not match', () => {
  const p = 'D:\\a\\write-email.md\nD:\\b\\draft-letter.md\nC:\\c\\reply-message.md';
  assert.equal(promptRun(p).stdout, '');
});

test('prompt: verb more than 60 characters before the noun does not match', () => {
  assert.equal(promptRun(`write ${'x'.repeat(70)} email`).stdout, '');
});

// ----- both modes -----

for (const mode of ['post-write', 'prompt']) {
  test(`${mode}: malformed JSON exits 0 with empty stdout`, () => {
    const r = run(mode, '{not json');
    assert.equal(r.status, 0);
    assert.equal(r.stdout, '');
  });

  test(`${mode}: empty stdin exits 0 with empty stdout`, () => {
    const r = run(mode, '');
    assert.equal(r.status, 0);
    assert.equal(r.stdout, '');
  });
}

test('unknown mode exits 0 with empty stdout', () => {
  const r = run('bogus', '{}');
  assert.equal(r.status, 0);
  assert.equal(r.stdout, '');
});

test('a broken hook.json falls back to the defaults', () => {
  const dir = mkdtempSync(join(tmpdir(), 'wlm-bad-'));
  mkdirSync(join(dir, 'voices', 'demo'), { recursive: true });
  writeFileSync(join(dir, 'voices', 'demo', 'hook.json'), '{broken');
  const r = write('D:\\work\\writing\\essay-block.md', 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_SKILL_DIR: dir });
  assert.equal(json(r).decision, 'block');
});


// ----- explanation and rejected files -----

const CTX = mkdtempSync(join(tmpdir(), 'wlm-ctx-'));
writeFileSync(join(CTX, 'expl.md'), 'The approved explanation.');
writeFileSync(join(CTX, 'rej.txt'), 'rejected phrase');
const ESSAY_BLOCK = 'D:\\work\\writing\\essay-block.md';

function skillWithHookJson(hookJson, files = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'wlm-ctxskill-'));
  mkdirSync(join(dir, 'voices', 'demo'), { recursive: true });
  writeFileSync(join(dir, 'voices', 'demo', 'profile.json'), '{}');
  writeFileSync(join(dir, 'voices', 'demo', 'hook.json'), JSON.stringify({ defaultRegister: 'essay', ...hookJson }));
  for (const [name, text] of Object.entries(files)) writeFileSync(join(dir, 'voices', 'demo', name), text);
  return dir;
}

test('hook.json explanationFile and rejectedFile are passed as paths relative to the voice folder', () => {
  const dir = skillWithHookJson(
    { explanationFile: 'explanation.md', rejectedFile: 'rejected.txt' },
    { 'explanation.md': 'x', 'rejected.txt': 'y' });
  const r = write(ESSAY_BLOCK, 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_SKILL_DIR: dir });
  assert.match(json(r).reason, /explanation=explanation\.md rejected=rejected\.txt/);
});

test('hook.json accepts absolute paths for both files', () => {
  const dir = skillWithHookJson({ explanationFile: join(CTX, 'expl.md'), rejectedFile: join(CTX, 'rej.txt') });
  const r = write(ESSAY_BLOCK, 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_SKILL_DIR: dir });
  assert.match(json(r).reason, /explanation=expl\.md rejected=rej\.txt/);
});

test('environment variables give the files and win over hook.json', () => {
  const dir = skillWithHookJson(
    { explanationFile: 'explanation.md', rejectedFile: 'rejected.txt' },
    { 'explanation.md': 'x', 'rejected.txt': 'y' });
  const r = write(ESSAY_BLOCK, 'Write', {
    ...FAKE_ENV, WRITE_LIKE_ME_SKILL_DIR: dir,
    WRITE_LIKE_ME_EXPLANATION: join(CTX, 'expl.md'), WRITE_LIKE_ME_REJECTED: join(CTX, 'rej.txt'),
  });
  assert.match(json(r).reason, /explanation=expl\.md rejected=rej\.txt/);
});

test('files that do not exist are not passed', () => {
  const dir = skillWithHookJson({ explanationFile: 'missing.md', rejectedFile: 'missing.txt' });
  const r = write(ESSAY_BLOCK, 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_SKILL_DIR: dir });
  assert.match(json(r).reason, /explanation=none rejected=none/);
});

test('without any configuration neither flag is passed', () => {
  assert.match(json(write(ESSAY_BLOCK)).reason, /explanation=none rejected=none/);
});

test('a REVIEW with drift lines prints the drift lines and counts them', () => {
  const o = json(write('D:\\work\\writing\\essay-drift.md'));
  const text = o.hookSpecificOutput.additionalContext;
  assert.match(text, /drift mean_sentence_words: observed 22\.1, target 10 to 16/);
  assert.doesNotMatch(text, /tricolon/);
  assert.equal(o.systemMessage, 'write-like-me: REVIEW on essay-drift.md (1 review hits)');
});

test('WRITE_LIKE_ME_PROFILE puts the voice folder, and its hook.json, anywhere', () => {
  const elsewhere = mkdtempSync(join(tmpdir(), 'wlm-else-'));
  writeFileSync(join(elsewhere, 'profile.json'), '{}');
  writeFileSync(join(elsewhere, 'hook.json'), JSON.stringify({ defaultRegister: 'memo', explanationFile: 'e.md' }));
  writeFileSync(join(elsewhere, 'e.md'), 'x');
  const r = write(ESSAY_BLOCK, 'Write', { ...FAKE_ENV, WRITE_LIKE_ME_PROFILE: join(elsewhere, 'profile.json') });
  assert.match(json(r).reason, /register=memo/);
  assert.match(json(r).reason, /explanation=e\.md/);
});
