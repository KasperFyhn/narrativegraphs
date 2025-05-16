from narrativegraph.mapping.common import Mapper


class LemmaMapper(Mapper):

    def __init__(self):
        super().__init__()

    def create_mapping(self, labels: list[str]) -> dict[str, str]:
        return {label: label for label in labels}
