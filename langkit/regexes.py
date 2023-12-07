from collections import defaultdict
from copy import deepcopy
from logging import getLogger

from langkit.pattern_loader import PatternLoader
from whylogs.experimental.core.udf_schema import register_dataset_udf
from langkit import LangKitConfig, lang_config, prompt_column, response_column
from whylogs.core.metrics.metrics import FrequentItemsMetric
from whylogs.core.resolvers import MetricSpec
from typing import Dict, Optional, Set
from langkit.whylogs.unreg import unregister_udfs

diagnostic_logger = getLogger(__name__)

pattern_loader = PatternLoader()
response_pattern_loader = PatternLoader()

_initialized = False


def has_patterns(text, regex_groups):
    if not _initialized:
        init()
    if regex_groups:
        for group in regex_groups:
            for expression in group["expressions"]:
                if expression.search(text):
                    return group["name"]
    return None


def _wrapper(column, groups):
    def wrappee(text):
        return [has_patterns(input, groups) for input in text[column]]

    return wrappee


_registered: Dict[str, Set[str]] = defaultdict(
    set
)  # _registered[schema_name] -> set of registered UDF names


def _register_udfs(config: Optional[LangKitConfig] = None, schema_name: str = ""):
    global _initialized
    _initialized = True
    global _registered
    unregister_udfs(_registered[schema_name], schema_name)
    _registered[schema_name] = set()
    if config is None:
        config = lang_config
    default_metric_name = "has_patterns"
    pattern_metric_name = config.metric_name_map.get(
        default_metric_name, default_metric_name
    )
    if pattern_loader.get_regex_groups() is not None:
        column = prompt_column
        udf_name = f"{column}.{pattern_metric_name}"
        register_dataset_udf(
            [column],
            udf_name=udf_name,
            metrics=[MetricSpec(FrequentItemsMetric)],
            schema_name=schema_name,
        )(_wrapper(column, pattern_loader.get_regex_groups()))
        _registered[schema_name].add(udf_name)

    if response_pattern_loader.get_regex_groups() is not None:
        column = response_column
        udf_name = f"{column}.{pattern_metric_name}"
        register_dataset_udf(
            [column],
            udf_name=udf_name,
            metrics=[MetricSpec(FrequentItemsMetric)],
            schema_name=schema_name,
        )(_wrapper(column, response_pattern_loader.get_regex_groups()))
        _registered[schema_name].add(udf_name)


def init(
    language: Optional[str] = None,
    pattern_file_path: Optional[str] = None,
    config: Optional[LangKitConfig] = None,
    response_pattern_file_path: Optional[str] = None,
    schema_name: str = "",
):
    global _initialized
    _initialized = True
    config = deepcopy(config or lang_config)
    if pattern_file_path:
        config.pattern_file_path = pattern_file_path
    if response_pattern_file_path:
        config.response_pattern_file_path = response_pattern_file_path

    global pattern_loader, response_pattern_loader
    pattern_loader = PatternLoader(config.pattern_file_path)
    response_pattern_loader = PatternLoader(config.response_pattern_file_path)

    _register_udfs(config, schema_name)
