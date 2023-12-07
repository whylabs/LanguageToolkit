from collections import defaultdict
from copy import deepcopy
from logging import getLogger
from typing import Callable, Dict, Optional, Set

from sentence_transformers import util
from whylogs.experimental.core.udf_schema import register_dataset_udf
from langkit import LangKitConfig, lang_config, prompt_column, response_column
from langkit.transformer import Encoder
from langkit.whylogs.unreg import unregister_udfs

_prompt = prompt_column
_response = response_column


_transformer_model = None

_initialized = False

diagnostic_logger = getLogger(__name__)


def prompt_response_similarity(text):
    if not _initialized:
        init()
    global _transformer_model

    if _transformer_model is None:
        raise ValueError(
            "response.relevance_to_prompt must have a transformer model initialized before use."
        )

    series_result = []
    for x, y in zip(text["prompt"], text["response"]):
        try:
            embedding_1 = _transformer_model.encode([x] if isinstance(x, str) else x)
            embedding_2 = _transformer_model.encode([y] if isinstance(y, str) else y)
            similarity = util.pytorch_cos_sim(embedding_1, embedding_2)
            series_result.append(similarity.item())
        except Exception as e:
            diagnostic_logger.warning(
                f"prompt_response_similarity encountered error {e} for text: {text}"
            )
            series_result.append(None)
    return series_result


_registered: Dict[str, Set[str]] = defaultdict(
    set
)  # _registered[schema_name] -> set of registered UDF names


def init(
    language: Optional[str] = None,
    transformer_name: Optional[str] = None,
    custom_encoder: Optional[Callable] = None,
    config: Optional[LangKitConfig] = None,
    schema_name: str = "",
):
    global _initialized
    _initialized = True
    global _registered
    unregister_udfs(_registered[schema_name], schema_name=schema_name)
    _registered[schema_name] = set()
    if transformer_name and custom_encoder:
        raise ValueError(
            "Only one of transformer_name or encoder can be specified, not both."
        )
    config = config or deepcopy(lang_config)
    global _transformer_model
    response_transformer_name = (
        transformer_name or config.response_transformer_name
    )  # not a bug :)
    transformer_name = transformer_name or config.transformer_name

    if transformer_name != response_transformer_name:  # can't evaluate across langauges
        _transformer_model = None
        return

    if transformer_name is None and custom_encoder is None:  # metric turned off
        _transformer_model = None
        return

    transformer_name = None if custom_encoder else transformer_name
    _transformer_model = Encoder(transformer_name, custom_encoder)
    register_dataset_udf(
        [prompt_column, response_column],
        f"{response_column}.relevance_to_{prompt_column}",
        schema_name=schema_name,
    )(prompt_response_similarity)
    _registered[schema_name].add(f"{response_column}.relevance_to_{prompt_column}")
