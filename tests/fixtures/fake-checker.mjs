// Fake voice checker for hook tests. The verdict follows the file name:
// "block", "review", "plain" (JSON without verdict, final token only), "crash", else pass.
import { basename } from 'node:path';

const args = process.argv.slice(2);
const file = args[0] ?? '';
const value = (flag) => {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : 'none';
};
const register = value('--register');
const profile = value('--profile') === 'none' ? 'none' : basename(value('--profile').replace(/\\/g, '/'));
const base = (flag) => basename(value(flag).replace(/\\/g, '/'));
const files = `explanation=${base('--explanation')} rejected=${base('--rejected')}`;
const name = basename(file.replace(/\\/g, '/')).toLowerCase();

function out(json, token) {
  console.log(JSON.stringify(json, null, 2));
  console.log(token);
}

if (name.includes('crash')) {
  console.error('boom');
  process.exit(2);
} else if (name.includes('block')) {
  out({
    verdict: 'BLOCK',
    hits: [
      { severity: 'block', rule: 'em-dash', excerpt: `a dash here (register=${register} profile=${profile} ${files})` },
      { severity: 'block', rule: 'tricolon', line: 'fast, clear, and good' },
      { severity: 'review', rule: 'hedge', excerpt: 'maybe' },
    ],
  }, 'VOICE_CHECK_BLOCK');
  process.exitCode = 1;
} else if (name.includes('drift')) {
  out({
    verdict: 'REVIEW',
    hits: [{ severity: 'info', rule: 'tricolon', excerpt: 'a, b, and c' }],
    drift: [{ metric: 'mean_sentence_words', observed: 22.1, target: [10, 16], severity: 'review' }],
  }, 'VOICE_CHECK_REVIEW');
} else if (name.includes('review')) {
  out({
    verdict: 'REVIEW',
    hits: [{ severity: 'review', rule: 'filler', excerpt: 'in order to' }],
  }, 'VOICE_CHECK_REVIEW');
} else if (name.includes('plain')) {
  console.log('not json at all');
  console.log('VOICE_CHECK_REVIEW');
} else {
  out({ verdict: 'PASS', hits: [] }, 'VOICE_CHECK_PASS');
}
