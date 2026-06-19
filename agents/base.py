import os
import time
import warnings
import httpx
import anthropic
from abc import ABC, abstractmethod
from pathlib import Path
from dotenv import load_dotenv

from config import cfg

load_dotenv()

MODEL = cfg.MODEL
MAX_ITERATIONS = cfg.MAX_ITERATIONS
MAX_RETRIES = cfg.MAX_RETRIES
RETRY_BASE_DELAY = cfg.RETRY_BASE_DELAY


def _make_client() -> anthropic.Anthropic:
    # 1.7: Validate API key at startup — fail fast rather than mid-build.
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. Add it to your .env file before running."
        )

    # SSL_CERT_FILE: path to a PEM bundle containing your corporate CA.
    # SSL_NO_VERIFY: set to "true" to disable SSL verification (corporate proxy workaround).
    ssl_cert_file = os.environ.get("SSL_CERT_FILE")
    ssl_no_verify = os.environ.get("SSL_NO_VERIFY", "").lower() == "true"

    if ssl_no_verify:
        warnings.warn("SSL verification disabled (SSL_NO_VERIFY=true).", stacklevel=2)
        http_client = httpx.Client(verify=False)
    elif ssl_cert_file:
        http_client = httpx.Client(verify=ssl_cert_file)
    else:
        http_client = None

    kwargs: dict = {"api_key": api_key}
    if http_client:
        kwargs["http_client"] = http_client
    return anthropic.Anthropic(**kwargs)


_client = _make_client()

_AGILE_TEAM_CONTEXT = """
## Squad & Silicon Valley Culture

Squad: an empowered, cross-functional product squad in the Silicon Valley tradition.
We build outcomes, not features. We ship continuously, measure everything, and iterate fast.
The squad owns both discovery (figuring out the right thing to build) and delivery (building it right).

## How We Work

- **OKR-driven**: Every sprint goal maps to an Objective and Key Result. If a task doesn't move a KR, deprioritize it.
- **Customer-obsessed**: The PM speaks for the user. Validate the problem before committing to the solution.
- **Outcome, not output**: "Feature shipped" is not success. "User problem solved" is success.
- **Bias for action**: Ship an MVP, learn, iterate. Waiting for perfect is the enemy of shipped.
- **Autonomous**: No one waits for permission to raise a problem or propose a solution.
- **Transparent**: Small, frequent updates beat big-bang surprises. Make work visible.

## Product Trio

The squad runs on a Product Trio at its core:
- **Product Manager** — owns the "what" and "why"; voice of the customer; defines success
- **Engineering Lead / Architect** — owns the "how"; technical strategy and feasibility
- **QA / SDET** — owns quality; tests that the "what" was actually delivered correctly

## Ceremonies

- **Daily Sync (15 min)**: Progress, blockers, handoffs — keep it tight, no status theater
- **Sprint Planning**: Commit to goals anchored to OKRs; break into tasks with acceptance criteria
- **Demo**: Show working software — not slides, not prototypes, not "it works on my machine"
- **Retro**: One concrete improvement per sprint; track whether last retro's action actually landed

## Definition of Done

- Code complete and peer-reviewed (PR merged)
- Unit + integration tests passing (coverage ≥ 80%)
- No known security vulnerabilities (bandit clean)
- Deployed to staging and smoke-tested
- PM has verified the implementation meets the acceptance criteria

## Communication Norms

- Be specific: "Login endpoint returns 401 when token expires" beats "auth is broken"
- Raise blockers immediately — one blocked task can stall the whole squad
- Disagree openly in discussion; commit fully once the decision is made
- Code reviews raise the quality bar — not egos. Focus on correctness, security, maintainability.

## Anthropic-Inspired Principles

This squad is also Anthropic-inspired. When values conflict, resolve them in this order:
  1. **Broadly safe** — support human oversight; never take irreversible actions without review
  2. **Broadly ethical** — honest, transparent, avoid unnecessary harm
  3. **Principled** — follow the squad's agreed norms and safety constitution
  4. **Helpful** — deliver value to users and the mission

Individual norms that flow from this:
- **Diplomatically honest, not dishonestly diplomatic**: say what you actually think. Flattery wastes everyone's time.
- **Calibrated uncertainty**: "I don't know" or "I'm not confident here" is always a valid answer — overconfidence is a defect.
- **Flag safety proactively**: if you spot a security risk, privacy issue, or ethical concern, raise it before being asked — even if it slows the sprint.
- **Low ego, high trust**: assume good faith from teammates; engage with ideas, not personalities.
- **Mission over prestige**: the goal is safe, reliable software that solves real problems — not clever code or impressive architecture.
- **Red-team your own work**: before marking anything done, ask "how could this fail or be misused?"
- **Document the why**: a decision without documented rationale is a future bug. The DecisionLog exists for a reason — use it.
- **Human oversight**: keep humans in the loop on consequential or irreversible actions. When in doubt, surface it rather than act unilaterally.
"""


def _last_text(messages: list) -> str:
    for msg in reversed(messages):
        content = msg.get("content", "")
        if isinstance(content, list):
            for block in content:
                if hasattr(block, "text"):
                    return block.text
        elif isinstance(content, str):
            return content
    return ""


class BaseAgent(ABC):
    """
    Foundation for all agents.
    - think(): single-turn reasoning (no tools)
    - act(): multi-turn plan-act-observe loop with tools
    """

    def __init__(
        self,
        name: str,
        roles: list[str],
        workspace: Path | None = None,
        model: str | None = None,
        max_history_turns: int | None = None,
    ):
        self.name = name
        self.roles = roles
        self.workspace = workspace
        self.model = model or MODEL
        self.max_history_turns = max_history_turns or cfg.MAX_HISTORY_TURNS
        self.messages: list = []
        self.memory_context: str = ""
        # 4.7: Token usage tracking
        self._token_usage: dict[str, int] = {"input": 0, "output": 0}
        self._system_prompt_text = self._create_system_prompt()

    @abstractmethod
    def _create_system_prompt(self) -> str:
        """Return the system prompt text for this agent. Must be implemented by subclasses."""

    # ── History pruning (2.1) ─────────────────────────────────────────────────

    def _prune_history(self) -> None:
        """
        Keep message history bounded to prevent context window overflow.
        Retains: first 2 messages (original task + first response) + last N pairs.
        """
        max_msgs = self.max_history_turns * 2
        if len(self.messages) > max_msgs:
            kept = self.messages[:2] + self.messages[-(max_msgs - 2):]
            print(f"[{self.name}] History pruned: {len(self.messages)} → {len(kept)} messages")
            self.messages = kept

    # ── Retry helper ─────────────────────────────────────────────────────────

    def _retry_call(self, fn):
        """
        Call fn() and retry up to MAX_RETRIES times on rate-limit (429) or
        API overload (529) responses, using exponential backoff.
        Any other APIStatusError is re-raised immediately.
        """
        for attempt in range(MAX_RETRIES + 1):
            try:
                return fn()
            except anthropic.APIStatusError as e:
                if e.status_code in (429, 529) and attempt < MAX_RETRIES:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    print(
                        f"[{self.name}] HTTP {e.status_code} "
                        f"(attempt {attempt + 1}/{MAX_RETRIES + 1}) — "
                        f"retrying in {delay:.0f}s"
                    )
                    time.sleep(delay)
                else:
                    raise
        raise RuntimeError(f"{self.name}: retry loop exhausted")

    def _build_system(self) -> list[dict]:
        blocks: list[dict] = [
            {
                "type": "text",
                "text": self._system_prompt_text,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if self.memory_context:
            blocks.append({"type": "text", "text": self.memory_context})
        return blocks

    def think(self, user_message: str) -> str:
        """Single-turn reasoning — no tools. Appends to conversation history."""
        self.messages.append({"role": "user", "content": user_message})
        system = self._build_system()
        messages = self.messages

        response = self._retry_call(lambda: _client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=messages,
        ))

        # 4.7: Accumulate token usage
        if hasattr(response, "usage"):
            self._token_usage["input"] += response.usage.input_tokens
            self._token_usage["output"] += response.usage.output_tokens

        text = "".join(b.text for b in response.content if b.type == "text")
        self.messages.append({"role": "assistant", "content": text})
        return text

    def act(self, task: str, tools: list[dict]) -> str:
        """
        Agentic tool-use loop. Agent reasons, calls tools, observes results,
        and continues until it reaches end_turn or MAX_ITERATIONS.
        Appends to self.messages so context accumulates within a session.
        """
        from tools.registry import execute_tool

        self.messages.append({"role": "user", "content": task})

        for _ in range(MAX_ITERATIONS):
            self._prune_history()  # 2.1: keep history bounded
            system = self._build_system()
            messages = self.messages
            model = self.model
            response = self._retry_call(lambda: _client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                messages=messages,
                tools=tools,
                tool_choice={"type": "auto"},
            ))

            # 4.7: Accumulate token usage
            if hasattr(response, "usage"):
                self._token_usage["input"] += response.usage.input_tokens
                self._token_usage["output"] += response.usage.output_tokens

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                return "".join(b.text for b in response.content if hasattr(b, "text"))

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result_str = execute_tool(block.name, dict(block.input))
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        })
                self.messages.append({"role": "user", "content": tool_results})
                continue

            break

        return f"[WARNING: iteration limit reached after {MAX_ITERATIONS} steps]\n\n{_last_text(self.messages)}"

    def invoke_skill(self, skill_name: str, task: str) -> str:
        from skills.registry import SkillRegistry
        return SkillRegistry.invoke(skill_name, task, workspace=self.workspace)

    def invoke_skill_chain(self, skill_names: list[str], task: str) -> dict[str, str]:
        from skills.registry import SkillRegistry
        return SkillRegistry.chain(skill_names, task, workspace=self.workspace)

    def receive_message(self, sender_name: str, content: str) -> str:
        return self.think(f"[Message from {sender_name}]: {content}")

    def daily_standup_update(self) -> str:
        return self.think(
            "Give your daily standup update. Be specific: what did you complete since yesterday, "
            "what are you working on today, and do you have any blockers or impediments?"
        )
