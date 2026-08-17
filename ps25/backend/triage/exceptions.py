"""P2 pipeline failures; HTTP mapping belongs to the P1 integration layer."""


class TriageError(Exception):
    """Base class for unrecoverable triage pipeline failures."""


class SttError(TriageError):
    pass


class UnderstandingError(TriageError):
    pass


class RetrievalError(TriageError):
    pass


class GenerationError(TriageError):
    pass
