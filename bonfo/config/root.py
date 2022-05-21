from dataclasses import dataclass, field

from dataclass_wizard import YAMLWizard
from dataclass_wizard.enums import LetterCase

from bonfo import __version__ as current_bonfo_version


@dataclass
class BoardConf(YAMLWizard, key_transform=LetterCase.SNAKE):  # type: ignore
    version: int = 1
    bonfo_version: str = field(default=current_bonfo_version)
    # pid_profiles: dict[int, PidTranslator] | None = None
    # rate_profiles: dict[int, RateTranslator] | None = None
    # pids: list[PidTranslator] | None = None
    # rates: list[RateTranslator] | None = None

    # TODO: version validation
