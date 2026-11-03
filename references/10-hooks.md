# 10. Activation Hooks for Claude Code

A skill that has to be remembered gets skipped. Two Claude Code hooks make the method run without a reminder. Both call `scripts/writing-gate-hook.mjs`, which uses only the Node standard library and always exits 0 so that it can never fail a session.

| Hook event | Mode | What it does |
|------------|------|--------------|
| `UserPromptSubmit` | `prompt` | Recognizes a request for a text that other people will read, or a question about one, and adds the method to the context. |
| `PostToolUse` on `Edit`, `Write` and `MultiEdit` | `post-write` | Runs `scripts/voice_check.py` on a reader text that was just written. A `VOICE_CHECK_BLOCK` verdict blocks and lists the block hits. A review verdict adds the review hits to the context. A pass prints one status line. |

When a text is written in chat and not to a file, the post-write hook cannot see it. Run the checker by hand before showing the text.

## The settings.json entries

Add both entries to `~/.claude/settings.json`. Replace `NAME` with the folder name of the voice under `voices/`. Replace `<SKILL_FOLDER>` with the folder this skill is installed in. On Windows that is, for example, `C:\\Users\\you\\.claude\\skills\\write-like-me` (backslashes doubled inside JSON). On macOS and Linux it is, for example, `$HOME/.claude/skills/write-like-me`.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"<SKILL_FOLDER>/scripts/writing-gate-hook.mjs\" prompt --voice NAME"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "node \"<SKILL_FOLDER>/scripts/writing-gate-hook.mjs\" post-write --voice NAME"
          }
        ]
      }
    ]
  }
}
```

The same command on Windows: `node "C:\Users\you\.claude\skills\write-like-me\scripts\writing-gate-hook.mjs" post-write --voice NAME`. The same command on macOS and Linux: `node "$HOME/.claude/skills/write-like-me/scripts/writing-gate-hook.mjs" post-write --voice NAME`.

If `settings.json` already has a `hooks` object, add the two arrays to it and keep the existing entries. The voice can also come from the environment variable `WRITE_LIKE_ME_VOICE`, and then `--voice NAME` is left out. When neither is set, the hook uses the voice in `voices/` if exactly one exists. With no voice, the checker runs the universal baseline without a profile.

## Where the hook looks

The voice folder is `voices/NAME/` inside the folder this skill is installed in. Any other location works when the hook is pointed at its profile, with the environment variable `WRITE_LIKE_ME_PROFILE` or with a `profile` entry in `voices/NAME/hook.json`.

- The checker is `scripts/voice_check.py`, found relative to the skill folder.
- The profile is `voices/NAME/profile.json`, or the file named by `WRITE_LIKE_ME_PROFILE` or by `profile` in `hook.json`. A missing profile means the universal baseline runs.
- The path rules are in `hook.json` in the folder of the profile in use. The file is optional.
- The approved explanation and the rejected phrases are passed to the checker when they are named, as described below.

## hook.json

All keys are optional. A key that is present replaces the default list. The `add` keys extend it.

```json
{
  "extensions": [".md", ".mdx", ".txt"],
  "include": ["writing", "draft", "cover", "letter", "linkedin"],
  "addInclude": ["field-notes"],
  "exclude": ["snapshot", "extracted", "transcript", "corpus", "fixtures"],
  "addExclude": ["archive"],
  "excludeNames": ["readme.md", "changelog.md"],
  "excludePrefixes": ["plan-"],
  "defaultRegister": "essay",
  "registers": { "letter": ["/letters/", "cover"], "post": ["/social/"] },
  "promptPhrases": ["tidy this up"],
  "explainFirst": true,
  "explanationFile": "explanation.md",
  "rejectedFile": "rejected.txt",
  "profile": "profile.json"
}
```

- `include` lists lowercase fragments. A file is a reader text when its full path contains one of them. The value `"*"` includes every file with a listed extension.
- `exclude` lists fragments that remove a file again. The defaults exclude evidence and input files (`snapshot`, `extracted`, `transcript`, `corpus`, `fixtures`, `evidence`), `node_modules`, `.git`, `.claude`, and the `voices/` folder of the skill.
- `excludeNames` and `excludePrefixes` remove files by name. The defaults cover README, CHANGELOG, LICENSE, SKILL, GATES, CONTRIBUTING, CLAUDE and AGENTS files and anything starting with `plan-`.
- `registers` maps a register name from the profile to path fragments. The first register whose fragment matches the path is used, and `defaultRegister` applies when none match.
- `promptPhrases` adds phrases that make the prompt hook fire. The hook already recognizes requests in English and in German, for example "Schreib eine Antwort auf die Mail" or "Wie klingt das?".
- `explainFirst` decides whether the prompt hook asks for the explanation step. The default is `true`. With `false` the hook asks for the text directly. A prompt that says "just write it", "write it directly", "skip the explanation", "without the explanation" or "no explanation first" turns the step off for that prompt, and "explain first", "explain it first" or "with the explanation" turns it on. The German phrases are "ohne Erklärung", "schreib es einfach" and "schreib es direkt" for off, and "erkläre zuerst" or "erst erklären" for on.
- `explanationFile` and `rejectedFile` name the approved explanation and the file of rejected phrases, one per line. A relative path is read from the voice folder and an absolute path is used as it is. When a file exists, the hook passes it to the checker as `--explanation` or `--rejected`, so `ADDITION` and `REPEATED_PHRASE` run on every written text. A file that does not exist is not passed.
- `profile` points at a `profile.json` in another location. A relative path is read from the folder of `hook.json`.

When the checker returns REVIEW, the hook prints each review hit and each drift line (metric, observed value, target). Drift lines are reports for the author. They are not edit orders for a text cut from an approved explanation.

## Environment variables

| Variable | Use |
|----------|-----|
| `WRITE_LIKE_ME_VOICE` | Voice name when `--voice` is not given. |
| `WRITE_LIKE_ME_SKILL_DIR` | Skill folder, when the script is not run from inside it. |
| `WRITE_LIKE_ME_CHECKER` | Path of a different `voice_check.py`. |
| `WRITE_LIKE_ME_PROFILE` | Path of a `profile.json` in any location. The hook reads `hook.json` from the same folder. |
| `WRITE_LIKE_ME_EXPLANATION` | Path of the approved explanation. Wins over `explanationFile` in `hook.json`. |
| `WRITE_LIKE_ME_REJECTED` | Path of the rejected phrases file. Wins over `rejectedFile` in `hook.json`. |
| `WRITE_LIKE_ME_EXPLAIN` | `off` or `on`. Wins over `explainFirst` in `hook.json`. A phrase in the prompt wins over both. |
| `WRITE_LIKE_ME_PYTHON` | Python executable. The default is `python`. |

## Testing the hooks

Run `node --test tests/*.test.mjs` from the skill folder. The tests use a fake checker, so they need no Python. To try the hook by hand, pipe a hook payload into it:

```
echo '{"tool_input":{"file_path":"/work/writing/essay.md"}}' | node scripts/writing-gate-hook.mjs post-write --voice NAME
```
