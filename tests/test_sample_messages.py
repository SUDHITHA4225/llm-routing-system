from __future__ import annotations

from pathlib import Path

from app.router import handle_message


class AlwaysUnclearLLM:
    def chat(self, **kwargs) -> str:
        if kwargs.get("force_json"):
            return '{"intent":"unclear","confidence":0.2}'
        return "Could you clarify the request?"


def test_assignment_sample_messages_do_not_crash(tmp_path: Path) -> None:
    messages = [
        "how do i sort a list of objects in python?",
        "explain this sql query for me",
        "This paragraph sounds awkward, can you help me fix it?",
        "I'm preparing for a job interview, any tips?",
        "what's the average of these numbers: 12, 45, 23, 67, 34",
        "Help me make this better.",
        "I need to write a function that takes a user id and returns their profile, but also i need help with my resume.",
        "hey",
        "Can you write me a poem about clouds?",
        "Rewrite this sentence to be more professional.",
        "I'm not sure what to do with my career.",
        "what is a pivot table",
        "fxi thsi bug pls: for i in range(10) print(i)",
        "How do I structure a cover letter?",
        "My boss says my writing is too verbose.",
    ]

    llm = AlwaysUnclearLLM()
    log_path = tmp_path / "route_log.jsonl"

    for msg in messages:
        out = handle_message(message=msg, llm_client=llm, log_path=log_path)
        assert out["intent"] == "unclear"
        assert "clarify" in out["response"].lower() or "help" in out["response"].lower()
