/**
 * guard-paths -- OpenCode plugin recipe (cross-harness migration D5 layer 4).
 * Port of .claude/hooks/guard-paths.sh (see briefs/guard-paths.md for the contract).
 *
 * Install: copy into <project>/.opencode/plugin/guard-paths.js
 * Enforcement: throws in tool.execute.before => the write tool call is vetoed.
 * Covers the tool layer only; shell writes bypass (X30 residual, same as Claude).
 * verification: UNRUN until a conformance record exists (COMPATIBILITY.md).
 */
import * as fs from "fs";
import * as path from "path";

const PROTECTED = [/\/\.raw\//, /\/private\//, /\/finance\//, /\/credentials\//];
const CONFIG_CLASS = [
  /\/\.claude\/hooks\//,
  /\/\.claude\/settings(\.local)?\.json$/,
  /\/\.claude\.json$/,
  /\/CLAUDE(\.local)?\.md$/,
  /\/AGENTS\.md$/,
  /\/\.agents\/(mcp|scripts|hooks)\//,
  /\/\.mcp\.json$/,
  /\/opencode\.json$/,
  /\/\.codex\/config\.toml$/,
];
const WRITE_TOOLS = new Set(["write", "edit", "patch", "multiedit"]);

export const GuardPaths = async ({ directory }) => {
  const armFlag = path.join(directory, ".claude", "state", "config-edit-armed");
  const logDir = path.join(directory, ".claude", "state");
  return {
    "tool.execute.before": async (input, output) => {
      const tool = String(input.tool || "").toLowerCase();
      if (!WRITE_TOOLS.has(tool)) return;
      const raw = String(
        (output.args && (output.args.filePath || output.args.file_path || output.args.path)) || ""
      );
      if (!raw) return;
      // RESOLVE before matching (2026-08-11 fix): OpenCode passes the model's
      // path argument UN-normalized. A relative path ("private/x.md") carries no
      // leading slash, so the /\/private\// class regexes never matched and the
      // veto was bypassable -- observed live: a fast model wrote private/veto-test.md
      // clean through the guard. resolve() also normalizes ".." traversal.
      const fp = path.resolve(directory, raw).replace(/\\/g, "/");
      for (const re of PROTECTED) {
        if (re.test(fp)) {
          throw new Error(
            "guard-paths: BLOCKED -- protected layer (agent writes forbidden). Path: " + fp
          );
        }
      }
      for (const re of CONFIG_CLASS) {
        if (re.test(fp)) {
          if (fs.existsSync(armFlag)) {
            fs.rmSync(armFlag); // one write per arm, consumed
            try {
              fs.mkdirSync(logDir, { recursive: true });
              fs.appendFileSync(
                path.join(logDir, "bypasses-" + new Date().toISOString().slice(0, 10) + ".log"),
                new Date().toISOString() +
                  " guard-paths(opencode) CONFIG-EDIT allowed (armed, flag consumed): " +
                  fp +
                  "\n"
              );
            } catch (e) {
              /* logging is best-effort; the allow already happened */
            }
            return;
          }
          throw new Error(
            "guard-paths: BLOCKED -- config/hook/settings surface (X26). Deliberate edit: create .claude/state/config-edit-armed and retry (one write per arm). Path: " + fp
          );
        }
      }
    },
  };
};
