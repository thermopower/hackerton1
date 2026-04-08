import { execSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";

/**
 * Harness hooks plugin — bridges existing .claude/hooks/*.sh scripts
 * to OpenCode's plugin event system.
 *
 * Claude Code 매핑:
 *   SessionStart               → session.created
 *   SubagentStop(sprint-builder)    → session.idle + status:implemented 감지
 *   SubagentStop(evaluator)         → session.idle + evaluation-report 변경 감지
 *   SubagentStop(reviewer)          → session.idle + review-notes 변경 감지
 *   SubagentStop(integration-fixer) → session.idle + fix_attempt 변경 감지
 *   SubagentStop(retrospective)     → session.idle + learnings 변경 감지
 */

function runHook(script, label) {
  if (!existsSync(script)) return null;
  try {
    const output = execSync(`bash ${script}`, {
      timeout: 120_000,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });
    return output;
  } catch (e) {
    console.error(`[harness:${label}] exit ${e.status}`);
    return null;
  }
}

function readStatus(file) {
  if (!existsSync(file)) return "none";
  const text = readFileSync(file, "utf-8");
  const match = text.match(/^status:\s*(.+)$/m);
  return match ? match[1].trim() : "none";
}

function readField(file, field) {
  if (!existsSync(file)) return null;
  const text = readFileSync(file, "utf-8");
  const re = new RegExp(`^${field}:\\s*(.+)$`, "m");
  const match = text.match(re);
  return match ? match[1].trim() : null;
}

// Track last-seen states to detect changes
let prevContractStatus = null;
let prevEvalStatus = null;
let prevReviewStatus = null;
let prevLearningsStatus = null;
let prevFixAttempt = null;

function detectAndRunHooks() {
  const contractStatus = readStatus(".claude-state/sprint-contract.md");
  const evalStatus = readStatus(".claude-state/evaluation-report.md");
  const reviewStatus = readStatus(".claude-state/review-notes.md");
  const learningsStatus = readStatus(".claude-state/learnings.md");
  const fixAttempt = readField(".claude-state/sprint-contract.md", "fix_attempt");

  // sprint-builder just finished (status changed to implemented)
  if (contractStatus === "implemented" && prevContractStatus !== "implemented") {
    runHook(".claude/hooks/check-smoke.sh", "check-smoke");
  }

  // evaluator or retrospective just finished (eval/learnings status changed)
  if (evalStatus !== "none" && prevEvalStatus !== evalStatus) {
    runHook(".claude/hooks/check-output.sh", "check-output");
  }
  if (learningsStatus !== "none" && prevLearningsStatus !== learningsStatus) {
    runHook(".claude/hooks/check-output.sh", "check-output");
  }

  // reviewer just finished (review-notes status changed)
  if (reviewStatus === "reviewed" && prevReviewStatus !== "reviewed") {
    runHook(".claude/hooks/check-output.sh", "check-output");
    runHook(".claude/hooks/trigger-retrospective.sh", "trigger-retro");
  }

  // integration-fixer just finished (fix_attempt changed)
  if (fixAttempt !== null && fixAttempt !== prevFixAttempt) {
    runHook(".claude/hooks/track-fix-attempt.sh", "track-fix-attempt");
  }

  // Update previous state
  prevContractStatus = contractStatus;
  prevEvalStatus = evalStatus;
  prevReviewStatus = reviewStatus;
  prevLearningsStatus = learningsStatus;
  prevFixAttempt = fixAttempt;
}

export default function harnessHooks(context) {
  return {
    event: async (event) => {
      if (event.type === "session.created") {
        // Capture initial state
        prevContractStatus = readStatus(".claude-state/sprint-contract.md");
        prevEvalStatus = readStatus(".claude-state/evaluation-report.md");
        prevReviewStatus = readStatus(".claude-state/review-notes.md");
        prevLearningsStatus = readStatus(".claude-state/learnings.md");
        prevFixAttempt = readField(".claude-state/sprint-contract.md", "fix_attempt");

        runHook(".claude/hooks/session-start.sh", "session-start");
      }

      if (event.type === "session.idle") {
        detectAndRunHooks();
      }
    },
  };
}
