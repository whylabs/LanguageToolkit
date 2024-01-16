from copy import deepcopy
from presidio_analyzer import AnalyzerEngine
from whylogs.experimental.core.udf_schema import (
    register_dataset_udf
)
import pandas as pd
from typing import Dict, List, Optional
from langkit import LangKitConfig, lang_config, prompt_column, response_column
from langkit.pattern_loader import PresidioEntityLoader
from langkit.utils import _unregister_metric_udf
from whylogs.core.metrics.metrics import FrequentItemsMetric
from whylogs.core.resolvers import MetricSpec

_registered: List[str] = []

entity_loader = PresidioEntityLoader()


# entities = ["PHONE_NUMBER", "US_PASSPORT"]
analyzer = AnalyzerEngine()


def analyze_pii(text: str) -> List[Dict[str, str]]:
    global analyzer
    global entity_loader

    entities = entity_loader.get_entities()
    results = analyzer.analyze(
        text=text,
        entities=entities,
        language="en",
    )
    dict_results = [
        {
            "type": f"{ent.entity_type}",
            "start": f"{ent.start}",
            "end": f"{ent.end}",
            "score": f"{ent.score}",
        } for ent in results
    ]
    return dict_results


def _wrapper(column):
    def wrappee(text):
        return [analyze_pii(input) for input in text[column]]

    return wrappee


def _register_udfs(config: Optional[LangKitConfig] = None):
    from whylogs.experimental.core.udf_schema import _resolver_specs

    global _registered
    if _registered and config is None:
        return
    if config is None:
        config = lang_config
    default_metric_name = "pii_presidio"
    entity_metric_name = config.metric_name_map.get(
        default_metric_name, default_metric_name
    )

    for old in _registered:
        _unregister_metric_udf(old_name=old)
        if (
            _resolver_specs is not None
            and isinstance(_resolver_specs, Dict)
            and isinstance(_resolver_specs[""], List)
        ):
            _resolver_specs[""] = [
                spec for spec in _resolver_specs[""] if spec.column_name != old
            ]
    _registered = []

    if entity_loader.get_entities() is not None:
        for column in [prompt_column, response_column]:
            udf_name = f"{column}.{entity_metric_name}"
            register_dataset_udf(
                [column],
                udf_name=udf_name,
                metrics=[MetricSpec(FrequentItemsMetric)],
            )(_wrapper(column))
            _registered.append(udf_name)


def init(
    entities_file_path: Optional[str] = None, config: Optional[LangKitConfig] = None
):
    config = deepcopy(config or lang_config)
    if entities_file_path:
        config.pattern_file_path = entities_file_path

    global entity_loader
    entity_loader = PresidioEntityLoader(config)
    entity_loader.update_entities()

    _register_udfs(config)


init()
