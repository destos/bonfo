from construct import IfThenElse, Optional

from bonfo.msp.versions import MSPVersions


class MSPVersion(IfThenElse):
    def __init__(self, thensubcon, version_added: MSPVersions, elsesubcon=None) -> None:
        self.version_added = version_added
        if elsesubcon is None:
            elsesubcon = Optional(thensubcon)
        super().__init__(self.version_checker, thensubcon, elsesubcon)

    def version_checker(self, context):
        msp: MSPVersions = context.get("msp", None)
        # Some way of getting to parent context? forget how
        msp: MSPVersions = context.get("__msp", None)
        if msp is not None:
            return msp.value >= self.version_added.value
        return True
