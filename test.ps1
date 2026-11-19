failure_type = type(exc).__name__
logger.warning(
    "%s: peer refinement failed (%s: %s); preserving its initial findings",
    self.name, failure_type, exc
)