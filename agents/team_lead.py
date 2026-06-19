import json
import re
from pathlib import Path
from agents.base import BaseAgent, _AGILE_TEAM_CONTEXT
from tools.registry import get_tools_for_role


class TeamLead(BaseAgent):
    """
    AI-powered Agile Team Lead / Scrum Master.
    """

    def _create_system_prompt(self) -> str:
        roles_text = "\n".join(f"- {r}" for r in self.roles)
        return f"""You are {self.name}, the Agile Team Lead and Scrum Master for a software development team.

## Your Role

You are a servant leader who makes the team more effective. You do not manage people — you remove
the obstacles that slow them down. You facilitate rather than direct. You synthesize information
from across the team to surface patterns, risks, and opportunities that individuals might miss.
You are equally comfortable talking about technical blockers, team dynamics, and delivery risk.

You hold the team accountable to agile principles without being dogmatic. You adapt the process
to the team's needs, not the other way around. You measure success by the team's ability to
consistently deliver valuable, working software.

## Your Responsibilities in This Sprint

{roles_text}

## How You Facilitate

Daily Standup:
- Keep it to 15 minutes — it is a synchronization event, not a status report to you
- Listen for hidden blockers in vague updates ("still working on X" for two days straight)
- Park detailed problem-solving for after the standup; note it as a follow-up item
- Summarize key themes and surface the most important action items for the day

Sprint Retrospective:
- Create psychological safety — people must feel safe to name real problems
- Focus on systems and processes, not individuals
- Ensure action items are specific, owned, and time-boxed — "we should communicate better" is not an action item
- Balance celebrating wins with addressing improvements

Impediment Removal:
- Distinguish between blockers (stopping work now) and risks (may stop work soon)
- Escalate organizational impediments quickly — do not let the team wait
- Follow up on impediments you have taken ownership of — never drop them silently

Performance Assessment:
- Use quantitative signals (velocity, escaped defects, cycle time) alongside qualitative observations
- Be honest about underperformance — vague praise does not help anyone improve
- Frame feedback in terms of team outcomes, not individual blame

{_AGILE_TEAM_CONTEXT}

## Response Style

Respond as {self.name} — facilitative, outcomes-focused, and candid. In standup facilitation,
synthesize rather than repeat. In retrospectives, name real patterns. In impediment removal,
be action-oriented. In performance assessment, be honest and specific.
"""

    def facilitate_standup(self, team_updates: list[tuple[str, str]]) -> str:
        formatted = "\n\n".join(
            f"**{name}**: {update}" for name, update in team_updates
        )
        return self.think(
            f"You are facilitating the daily standup. Here are the team updates:\n\n{formatted}\n\n"
            "As Scrum Master: synthesize the key themes, call out any blockers or risks you heard "
            "(including implicit ones hidden in vague updates), identify any cross-team dependencies, "
            "and state the most important action items to follow up on today."
        )

    def identify_impediments(self, situation: str) -> str:
        return self.think(
            f"Review this situation for impediments:\n\n{situation}\n\n"
            "Identify: what is blocked or at risk, the impact on the sprint goal if unresolved, "
            "and your specific plan to remove or escalate each impediment. "
            "Distinguish blockers (stopping work now) from risks (may impact delivery)."
        )

    def retrospective(self, sprint_summary: str) -> str:
        return self.think(
            f"Facilitate a sprint retrospective based on this sprint summary:\n\n{sprint_summary}\n\n"
            "Structure your facilitation as:\n"
            "1. What went well (specific, concrete examples)\n"
            "2. What needs improvement (honest assessment of the real issues, not surface symptoms)\n"
            "3. Action items (specific, owned, time-boxed — at least 2-3 concrete actions)\n"
            "Be honest. Do not soften real problems into vague positivity."
        )

    def assess_performance(self, activities: str) -> str:
        return self.think(
            f"Assess the team's performance based on these sprint activities:\n\n{activities}\n\n"
            "Provide: an honest summary of delivery quality and consistency, specific strengths "
            "observed, specific areas needing improvement with concrete recommendations, "
            "and your overall assessment of team health and trajectory."
        )

    def create_backlog_from_architecture(self, workspace: Path) -> list[dict]:
        """Load tasks from architecture artifacts. Falls back to direct file read if LLM parse fails."""
        tools = get_tools_for_role("team_lead")
        try:
            result = self.act(
                "Read ARCHITECTURE.md and backlog_tasks.json from the workspace, "
                "then return ONLY a valid JSON array of tasks with no surrounding text:\n"
                '[{"title": "...", "description": "...", "depends_on": []}, ...]',
                tools,
            )
            tasks = _extract_json_tasks(result)
            if tasks:
                return tasks
        except Exception:
            pass
        # Fallback: read the file directly (Architect wrote it)
        tasks_file = workspace / "backlog_tasks.json"
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "tasks" in data:
                    return data["tasks"]
            except (json.JSONDecodeError, KeyError):
                pass
        return []

    def assign_next_task(self, backlog, developer_name: str):
        """
        Dependency-aware assignment (2.2): only assigns tasks whose depends_on
        tasks are all in a done/force_completed state.
        """
        done_titles = {
            t.title for t in backlog._tasks
            if t.status in ("done", "force_completed")
        }
        eligible = [
            t for t in backlog.get_pending()
            if all(dep in done_titles for dep in (t.depends_on or []))
        ]
        if not eligible:
            return None
        return backlog.assign_task(eligible[0].id, developer_name)


def _extract_json_tasks(text: str) -> list[dict]:
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        if isinstance(data, list):
            return [t for t in data if isinstance(t, dict) and "title" in t]
    except json.JSONDecodeError:
        pass
    return []
