#!/usr/bin/env node
// Claude Code hooks for the write-like-me skill.
//
//   node writing-gate-hook.mjs post-write [--voice NAME]   (PostToolUse on Edit|Write|MultiEdit)
//   node writing-gate-hook.mjs prompt     [--voice NAME]   (UserPromptSubmit)
//
// Reads the hook JSON from stdin, prints at most one JSON line, always exits 0.
// The voice comes from --voice or WRITE_LIKE_ME_VOICE. With neither, a single voice in voices/ is used,
// and with none the checker runs the universal baseline. The profile is voices/<voice>/profile.json and
// the path rules are in voices/<voice>/hook.json. Node standard library only.
//
// Environment overrides, mainly for tests: WRITE_LIKE_ME_VOICE, WRITE_LIKE_ME_SKILL_DIR,
// WRITE_LIKE_ME_CHECKER, WRITE_LIKE_ME_PROFILE, WRITE_LIKE_ME_PYTHON.

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { basename, dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const CHECK_TIMEOUT_MS = 20000;
const MAX_HITS = 8;

export const DEFAULT_CONFIG = {
  extensions: ['.md', '.mdx', '.txt'],
  include: [
    'writing', 'draft', 'cover', 'letter', 'linkedin', 'outreach', 'portfolio', 'essay', 'article',
    'blog', 'newsletter', 'email', 'listing', 'bio', 'about', 'copy', 'content', 'summar',
    'application', 'social',
  ],
  exclude: [
    'snapshot', 'extracted', 'transcript', 'corpus', 'fixtures', 'evidence', 'node_modules',
    '/.git/', '/voices/', '__pycache__', '/.claude/',
  ],
  excludeNames: [
    'readme.md', 'changelog.md', 'license.md', 'skill.md', 'gates.md', 'contributing.md',
    'claude.md', 'agents.md',
  ],
  excludePrefixes: ['plan-'],
  defaultRegister: null,
  registers: {},
  promptPhrases: [],
};

const PROMPT_CONTEXT =
  'This prompt asks for a text other people will read, or a judgment of one. ' +
  'write-like-me applies now, without being asked: read references/09-how-to-write.md, ' +
  'explain the subject to the author in chat first, then cut that explanation into the text, ' +
  'add nothing the request did not contain, and run the checker before showing it. ' +
  'If the author asked a yes or no question about a text, answer yes or no first and change nothing until the author says so.';

const REQUEST_VERBS =
  'write|draft|rewrite|revise|reword|proofread|polish|shorten|improve|reply|respond|answer|formulate|suggest';
const READER_NOUNS =
  'email|e-mail|mail|cover letter|letter|post|profile|bio|about|summary|overview|description|listing|' +
  'message|reply|response|answer|application|question|tagline|headline|caption|script|text|paragraph|' +
  'intro|introduction|statement|note to|outreach|dm|readme';
const VERB_NOUN_RE = new RegExp(
  `\\b(?:${REQUEST_VERBS})\\b[\\s\\S]{0,60}?\\b(?:${READER_NOUNS})\\b`, 'i');
const TRIGGER_PHRASES = [
  'how does this come across', 'how do i come across', 'is this good', 'does this sound',
  'sounds good', 'in your own words', 'what should i write', 'what can i write',
  'can you suggest what', 'proper english', 'grammar', 'make it shorter', 'too long',
  'on point', 'in my style', 'write like me', 'write-like-me', 'my voice',
];

// ---------- shared helpers ----------

function emit(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function readInput() {
  try {
    const raw = readFileSync(0, 'utf8');
    if (!raw.trim()) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch {
    return null;
  }
}

function skillDir() {
  return process.env.WRITE_LIKE_ME_SKILL_DIR || resolve(HERE, '..');
}

function voiceFromArgs(argv) {
  const i = argv.indexOf('--voice');
  return i >= 0 && argv[i + 1] ? argv[i + 1] : null;
}

export function resolveVoice(argv, dir = skillDir()) {
  const named = voiceFromArgs(argv) || process.env.WRITE_LIKE_ME_VOICE || null;
  if (named) return named;
  try {
    const voices = readdirSync(join(dir, 'voices'), { withFileTypes: true })
      .filter((d) => d.isDirectory() && existsSync(join(dir, 'voices', d.name, 'profile.json')))
      .map((d) => d.name);
    return voices.length === 1 ? voices[0] : null;
  } catch {
    return null;
  }
}

export function loadConfig(voice, dir = skillDir()) {
  const config = { ...DEFAULT_CONFIG };
  if (!voice) return config;
  let user = null;
  try {
    user = JSON.parse(readFileSync(join(dir, 'voices', voice, 'hook.json'), 'utf8'));
  } catch {
    return config;
  }
  if (!user || typeof user !== 'object') return config;
  const lists = ['extensions', 'include', 'exclude', 'excludeNames', 'excludePrefixes', 'promptPhrases'];
  for (const key of lists) {
    if (Array.isArray(user[key])) config[key] = user[key].map(String);
  }
  if (Array.isArray(user.addInclude)) config.include = [...config.include, ...user.addInclude.map(String)];
  if (Array.isArray(user.addExclude)) config.exclude = [...config.exclude, ...user.addExclude.map(String)];
  if (typeof user.defaultRegister === 'string') config.defaultRegister = user.defaultRegister;
  if (user.registers && typeof user.registers === 'object') config.registers = user.registers;
  return config;
}

// ---------- post-write mode ----------

export function extractFilePath(input) {
  const ti = input.tool_input ?? input.toolInput ?? {};
  const candidate = ti.file_path ?? ti.path ?? ti.filePath;
  return typeof candidate === 'string' && candidate ? candidate : null;
}

export function isReaderText(filePath, config = DEFAULT_CONFIG) {
  const norm = '/' + filePath.replace(/\\/g, '/').toLowerCase().replace(/^\/+/, '');
  const name = norm.slice(norm.lastIndexOf('/') + 1);
  const exts = config.extensions.map((e) => e.toLowerCase());
  if (!exts.includes(extname(name))) return false;
  if (config.excludeNames.map((n) => n.toLowerCase()).includes(name)) return false;
  if (config.excludePrefixes.some((p) => name.startsWith(p.toLowerCase()))) return false;
  if (config.exclude.some((m) => norm.includes(m.toLowerCase()))) return false;
  if (config.include.includes('*')) return true;
  return config.include.some((m) => norm.includes(m.toLowerCase()));
}

export function chooseRegister(filePath, config = DEFAULT_CONFIG) {
  const norm = filePath.replace(/\\/g, '/').toLowerCase();
  for (const [register, markers] of Object.entries(config.registers || {})) {
    if (Array.isArray(markers) && markers.some((m) => norm.includes(String(m).toLowerCase()))) return register;
  }
  return config.defaultRegister || null;
}

function parseCheckerOutput(stdout) {
  const lines = String(stdout ?? '').split(/\r?\n/);
  while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  if (!lines.length) return null;
  const last = lines[lines.length - 1].trim();
  const token = /^VOICE_CHECK_(PASS|REVIEW|BLOCK)$/.test(last) ? last.slice('VOICE_CHECK_'.length) : null;
  const body = token ? lines.slice(0, -1).join('\n') : lines.join('\n');
  let json = null;
  try {
    const parsed = JSON.parse(body);
    if (parsed && typeof parsed === 'object') json = parsed;
  } catch {
    json = null;
  }
  const fromJson = typeof json?.verdict === 'string'
    ? json.verdict.toUpperCase().replace(/^VOICE_CHECK_/, '')
    : null;
  const verdict = ['PASS', 'REVIEW', 'BLOCK'].includes(fromJson) ? fromJson : token;
  if (!verdict) return null;
  return { verdict, hits: Array.isArray(json?.hits) ? json.hits : [] };
}

function runChecker(filePath, register, voice, dir) {
  const python = process.env.WRITE_LIKE_ME_PYTHON || 'python';
  const checker = process.env.WRITE_LIKE_ME_CHECKER || join(dir, 'scripts', 'voice_check.py');
  const profile = process.env.WRITE_LIKE_ME_PROFILE || (voice ? join(dir, 'voices', voice, 'profile.json') : null);
  const args = [checker, filePath, '--json'];
  if (profile && existsSync(profile)) args.push('--profile', profile);
  if (register) args.push('--register', register);
  const res = spawnSync(python, args, { encoding: 'utf8', timeout: CHECK_TIMEOUT_MS, windowsHide: true });
  if (res.error) {
    const reason = res.error.code === 'ETIMEDOUT' ? 'timeout after 20 seconds' : res.error.message;
    return { error: reason };
  }
  const parsed = parseCheckerOutput(res.stdout);
  if (parsed) return parsed;
  const detail = String(res.stderr || '').trim().split(/\r?\n/).pop() || `exit code ${res.status}`;
  return { error: detail.slice(0, 200) };
}

function describeHit(hit) {
  if (typeof hit === 'string') return hit;
  if (!hit || typeof hit !== 'object') return '';
  const rule = hit.rule ?? hit.id ?? hit.name ?? 'rule';
  const keys = ['excerpt', 'text', 'snippet', 'match', 'context', 'message', 'line'];
  const key = keys.find((k) => typeof hit[k] === 'string' && hit[k]);
  const excerpt = key ? hit[key].replace(/\s+/g, ' ').trim().slice(0, 120) : '';
  return excerpt ? `${rule}: ${excerpt}` : String(rule);
}

function selectHits(hits, severity) {
  const matching = hits.filter((h) => h && h.severity === severity);
  return matching.length ? matching : hits;
}

function hitSummary(hits, severity) {
  const chosen = selectHits(hits, severity);
  const list = chosen.slice(0, MAX_HITS).map(describeHit).filter(Boolean).join(' | ');
  return { list, count: chosen.length };
}

function postWriteOutput(filePath, result) {
  const name = basename(filePath.replace(/\\/g, '/'));
  if (result.error) {
    return {
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: `write-like-me checker could not run on ${filePath}: ${result.error}. Run it by hand before showing the text.`,
      },
    };
  }
  if (result.verdict === 'BLOCK') {
    const { list, count } = hitSummary(result.hits, 'block');
    return {
      decision: 'block',
      reason: `write-like-me checker: VOICE_CHECK_BLOCK on ${filePath}. Fix every block hit, then write the file again. ${list}`.trim(),
      systemMessage: `write-like-me: BLOCK on ${name} (${count} block hits)`,
    };
  }
  if (result.verdict === 'REVIEW') {
    const { list, count } = hitSummary(result.hits, 'review');
    return {
      hookSpecificOutput: {
        hookEventName: 'PostToolUse',
        additionalContext: `write-like-me checker: VOICE_CHECK_REVIEW on ${filePath}. Resolve or justify each review hit in one line before showing the text. ${list}`.trim(),
      },
      systemMessage: `write-like-me: REVIEW on ${name} (${count} review hits)`,
    };
  }
  return { systemMessage: `write-like-me: PASS on ${name}` };
}

function runPostWrite(argv) {
  const input = readInput();
  if (!input) return;
  const filePath = extractFilePath(input);
  if (!filePath) return;
  const dir = skillDir();
  const voice = resolveVoice(argv, dir);
  const config = loadConfig(voice, dir);
  if (!isReaderText(filePath, config)) return;
  emit(postWriteOutput(filePath, runChecker(filePath, chooseRegister(filePath, config), voice, dir)));
}

// ---------- prompt mode ----------

export function isMostlyCode(prompt) {
  const lines = prompt.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return false;
  let inFence = false;
  let codeLines = 0;
  for (const line of lines) {
    const isFence = line.startsWith('```');
    if (isFence) {
      inFence = !inFence;
      codeLines += 1;
    } else if (inFence || /^([A-Za-z]:[\\/]|\/|~\/|\.{1,2}[\\/]|\{)/.test(line)) {
      codeLines += 1;
    }
  }
  return codeLines / lines.length > 0.3;
}

export function promptAsksForReaderText(prompt, config = DEFAULT_CONFIG) {
  const text = String(prompt ?? '').trim();
  if (text.length < 8) return false;
  if (isMostlyCode(text)) return false;
  const lower = text.toLowerCase();
  if ([...TRIGGER_PHRASES, ...(config.promptPhrases || []).map((p) => p.toLowerCase())].some((p) => lower.includes(p))) {
    return true;
  }
  return VERB_NOUN_RE.test(text);
}

function runPrompt(argv) {
  const input = readInput();
  if (!input || typeof input.prompt !== 'string') return;
  const config = loadConfig(resolveVoice(argv));
  if (!promptAsksForReaderText(input.prompt, config)) return;
  emit({ hookSpecificOutput: { hookEventName: 'UserPromptSubmit', additionalContext: PROMPT_CONTEXT } });
}

// ---------- entry ----------

function main() {
  const [mode, ...rest] = process.argv.slice(2);
  try {
    if (mode === 'post-write') runPostWrite(rest);
    else if (mode === 'prompt') runPrompt(rest);
  } catch {
    // Hooks must never fail the session.
  }
  process.exitCode = 0;
}

if (process.argv[1] && resolve(fileURLToPath(import.meta.url)).toLowerCase() === resolve(process.argv[1]).toLowerCase()) main();
