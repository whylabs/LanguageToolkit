import json
import re
from logging import getLogger

from whylogs.experimental.core.udf_schema import register_dataset_udf
from . import LangKitConfig, lang_config, prompt_column, response_column
from whylogs.core.metrics.metrics import FrequentItemsMetric
from whylogs.core.resolvers import MetricSpec
from whylogs.core.stubs import pd
from typing import Optional

diagnostic_logger = getLogger(__name__)


class PatternLoader:
    def __init__(self, config: Optional[LangKitConfig] = None):
        self.config = config or lang_config
        self.regex_groups = self.load_patterns()

    def load_patterns(self):
        json_path = self.config.pattern_file_path
        try:
            skip = False
            with open(json_path, "r") as myfile:
                _REGEX_GROUPS = json.load(myfile)
            regex_groups = []
            for group in _REGEX_GROUPS:
                compiled_expressions = []
                for expression in group["expressions"]:
                    compiled_expressions.append(re.compile(expression))

                regex_groups.append(
                    {"name": group["name"], "expressions": compiled_expressions}
                )
                diagnostic_logger.info(f"Loaded regex pattern for {group['name']}")
        except FileNotFoundError:
            skip = True
            diagnostic_logger.warning(f"Could not find {json_path}")
        except json.decoder.JSONDecodeError as json_error:
            skip = True
            diagnostic_logger.warning(f"Could not parse {json_path}: {json_error}")
        if not skip:
            return regex_groups
        return None

    def set_config(self, config: LangKitConfig):
        self.config = config

    def update_patterns(self):
        self.regex_groups = self.load_patterns()

    def get_regex_groups(self):
        return self.regex_groups


pattern_loader = PatternLoader()


def has_patterns(text):
    regex_groups = pattern_loader.get_regex_groups()
    result = []
    if regex_groups:
        index = (
            text.columns[0] if isinstance(text, pd.DataFrame) else list(text.keys())[0]
        )
        for input in text[index]:
            matched = None
            for group in regex_groups:
                for expression in group["expressions"]:
                    if expression.search(input):
                        matched = matched or group["name"]
                        break
                if matched is not None:
                    break

            result.append(matched)

    return result


_registered = False


def _register_udfs():
    global _registered
    if _registered:
        return

    if pattern_loader.get_regex_groups() is not None:
        _registered = True
        for column in [prompt_column, response_column]:
            register_dataset_udf(
                [column],
                udf_name=f"{column}.has_patterns",
                metrics=[MetricSpec(FrequentItemsMetric)],
            )(has_patterns)


def init(
    pattern_file_path: Optional[str] = None, config: Optional[LangKitConfig] = None
):
    config = config or lang_config
    if pattern_file_path:
        config.pattern_file_path = pattern_file_path
        pattern_loader.set_config(config)
        pattern_loader.update_patterns()
    else:
        pattern_loader.set_config(config)
        pattern_loader.update_patterns()

    _register_udfs()


init()
