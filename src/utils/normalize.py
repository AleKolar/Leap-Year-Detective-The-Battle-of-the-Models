def to_md(evidence):
    return "\n\n".join(
        f"### {e['model']}\n\n```python\n{e['content']}\n```"
        for e in evidence
    )