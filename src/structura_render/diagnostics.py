"""Bounded, operation-local notices about geometry approximations."""

import warnings
from contextlib import contextmanager
from contextvars import ContextVar


class RenderWarning(UserWarning):
    """The rendered geometry contains reported approximations or omissions."""


_active = ContextVar("structura_render_diagnostics", default=None)


def report_issue(kind, subject):
    issues = _active.get()
    if issues is None:
        return
    examples = issues.setdefault(kind, {})
    subject = str(subject)[:180]
    if subject in examples or len(examples) < 5:
        examples[subject] = None
    else:
        examples["…"] = None


@contextmanager
def render_diagnostics(*, strict=False):
    issues = {}
    token = _active.set(issues)
    try:
        yield
    finally:
        _active.reset(token)
    if issues:
        message = "Render approximations: " + "; ".join(
            f"{kind}: {', '.join(sorted(examples))}" for kind, examples in sorted(issues.items())
        )
        if strict:
            raise ValueError(message)
        warnings.warn(message, RenderWarning, stacklevel=3)
