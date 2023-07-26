from dataclasses import dataclass, field

import pkg_resources


@dataclass
class LangKitConfig:
    pattern_file_path: str = pkg_resources.resource_filename(
        __name__, "pattern_groups.json"
    )
    transformer_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    theme_file_path: str = pkg_resources.resource_filename(__name__, "themes.json")
    prompt_column: str = "prompt"
    response_column: str = "response"
    topics: list = field(
        default_factory=lambda: [
            "law",
            "finance",
            "medical",
            "education",
            "politics",
            "support",
        ]
    )
    nlp_scores: list = field(
        default_factory=lambda: [
            "bleu",
            "rouge",
            "meteor",
        ]
    )
    reference_corpus: str = ""


def package_version(package: str = __package__) -> str:
    """Calculate version number based on pyproject.toml"""
    try:
        from importlib import metadata

        version = metadata.version(package)
    except metadata.PackageNotFoundError:
        version = f"{package} is not installed."

    return version


__version__ = package_version()
