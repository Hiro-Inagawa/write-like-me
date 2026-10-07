# 10. Activation Hooks for Claude Code

A skill that has to be remembered gets skipped. Two Claude Code hooks make the method run without a reminder. Both call `scripts/writing-gate-hook.mjs`, which uses only the Node standard library and always exits 0 so that it can never fail a session.

| Hook event | Mode | What it does |
|------------|------|--------------|
| `UserPromptSubmit` | `prompt` | Recognizes a request for a text that other people will read, or a question about one, and adds the method to the context. |
| `PostToolUse` on `Edit`, `Write` and `MultiEdit` | `post-write` | Runs `scripts/voice_check.py` on a reader text that was just written. A `VOICE_CHECK_BLOCK` verdict blocks and lists the block hits. A review verdict adds the review hits to the context. A pass prints one status line. |

When a text is written in chat and not to a file, the post-write hook cannot see it. Run the checker by hand before showing the text.

## The settings.json entries

Add both entries to `~/.claude/settings.json`. Replace `NAME` with the folder name of the voice under `voices/`. The path assumes the skill is installed at `~/.claude/skills/write-like-me`. Change it when the skill lives elsewhere.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"$HOME/.claude/skills/write-like-me/scripts/writing-gate-hook.mjs\" prompt --voice NAME"
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
            "command": "node \"$HOME/.claude/skills/write-like-me/scripts/writing-gate-hook.mjs\" post-write --voice NAME"
          }
        ]
      }
    ]
  }
}
```

If `settings.json` already has a `hooks` object, add the two arrays to it and keep the existing entries. The voice can also come from the environment variable `WRITE_LIKE_ME_VOICE`, and then `--voice NAME` is left out. When neither is set, the hook uses the voice in `voices/` if exactly one exists. With no voice, the checker runs the universal baseline without a profile.

## Where the hook looks

- The checker is `scripts/voice_check.py`, found relative to the skill folder.
- The profile is `voices/NAME/profile.json`. A missing profile means the universal baseline runs.
- The path rules are in `voices/NAME/hook.json`. The file is optional.

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
  "promptPhrases": ["tidy this up"]
}
```

- `include` lists lowercase fragments. A file is a reader text when its full path contains one of them. The value `"*"` includes every file with a listed extension.
- `exclude` lists fragments that remove a file again. The defaults exclude evidence and input files (`snapshot`, `extracted`, `transcript`, `corpus`, `fixtures`, `evidence`), `node_modules`, `.git`, `.claude`, and the `voices/` folder of the skill.
- `excludeNames` and `excludePrefixes` remove files by name. The defaults cover README, CHANGELOG, LICENSE, SKILL, GATES, CONTRIBUTING, CLAUDE and AGENTS files and anything starting with `plan-`.
- `registers` maps a register name from the profile to path fragments. The first register whose fragment matches the path is used, and `defaultRegister` applies when none match.
- `promptPhrases` adds phrases that make the prompt hook fire.

## Environment variables

| Variable | Use |
|----------|-----|
| `WRITE_LIKE_ME_VOICE` | Voice name when `--voice` is not given. |
| `WRITE_LIKE_ME_SKILL_DIR` | Skill folder, when the script is not run from inside it. |
| `WRITE_LIKE_ME_CHECKER` | Path of a different `voice_check.py`. |
| `WRITE_LIKE_ME_PROFILE` | Path of a different `profile.json`. |
| `WRITE_LIKE_ME_PYTHON` | Python executable. The default is `python`. |

## Testing the hooks

Run `node --test tests/*.test.mjs` from the skill folder. The tests use a fake checker, so they need no Python. To try the hook by hand, pipe a hook payload into it:

```
echo '{"tool_input":{"file_path":"/work/writing/essay.md"}}' | node scripts/writing-gate-hook.mjs post-write --voice NAME
```
