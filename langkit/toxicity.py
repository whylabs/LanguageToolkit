from collections import defaultdict
from copy import deepcopy
from typing import Dict, Optional, Set

from whylogs.experimental.core.udf_schema import register_dataset_udf
from langkit import LangKitConfig, lang_config, prompt_column, response_column
from langkit.translator import Translator, translated_udf
from langkit.whylogs.unreg import unregister_udfs

import os
import torch

_USE_CUDA = torch.cuda.is_available() and not bool(
    os.environ.get("LANGKIT_NO_CUDA", False)
)
_device = 0 if _USE_CUDA else -1

_toxicity_tokenizer = None
_toxicity_pipeline = None

_response_toxicity_tokenizer = None
_response_toxicity_pipeline = None

_initialized = False

PROMPT_TRANSLATOR: Optional[Translator] = None
RESPONSE_TRANSLATOR: Optional[Translator] = None
TRANSLATOR: Optional[Translator] = None


def toxicity(text: str, pipeline, tokenizer) -> float:
    if not _initialized:
        init()
    pipeline = pipeline or _toxicity_pipeline
    tokenizer = tokenizer or _toxicity_tokenizer
    if pipeline is None or tokenizer is None:
        raise ValueError("toxicity score must initialize the pipeline first")

    result = pipeline(text, truncation=True, max_length=tokenizer.model_max_length)
    return (
        result[0]["score"] if result[0]["label"] == "toxic" else 1 - result[0]["score"]
    )


def _toxicity_wrapper(column, pipeline, tokenizer):
    return lambda text: [toxicity(t, pipeline, tokenizer) for t in text[column]]


_registered: Dict[str, Set[str]] = defaultdict(
    set
)  # _registered[schema_name] -> set of registered UDF names


def init(
    language: Optional[str] = None,
    model_path: Optional[str] = None,
    config: Optional[LangKitConfig] = None,
    response_model_path: Optional[str] = None,
    schema_name: str = "",
):
    global _initialized
    _initialized = True
    global _registered
    unregister_udfs(_registered[schema_name], schema_name=schema_name)
    _registered[schema_name] = set()
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        TextClassificationPipeline,
    )

    translators = {
        prompt_column: TRANSLATOR or PROMPT_TRANSLATOR,
        response_column: TRANSLATOR or RESPONSE_TRANSLATOR,
    }
    config = config or deepcopy(lang_config)
    model_path = model_path or config.toxicity_model_path
    global _toxicity_tokenizer, _toxicity_pipeline
    if model_path is None:
        _toxicity_pipeline = None
    else:
        _toxicity_tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        _toxicity_pipeline = TextClassificationPipeline(
            model=model, tokenizer=_toxicity_tokenizer, device=_device
        )
        register_dataset_udf(
            [prompt_column], f"{prompt_column}.toxicity", schema_name=schema_name
        )(
            translated_udf(translators)(
                _toxicity_wrapper(
                    prompt_column, _toxicity_pipeline, _toxicity_tokenizer
                )
            )
        )
        _registered[schema_name].add(f"{prompt_column}.toxicity")

    model_path = response_model_path or config.response_toxicity_model_path
    global _response_toxicity_tokenizer, _response_toxicity_pipeline
    if model_path is None:
        _response_toxicity_pipeline = None
    else:
        _response_toxicity_tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        _response_toxicity_pipeline = TextClassificationPipeline(
            model=model, tokenizer=_response_toxicity_tokenizer, device=_device
        )
        register_dataset_udf(
            [response_column], f"{response_column}.toxicity", schema_name=schema_name
        )(
            translated_udf(translators)(
                _toxicity_wrapper(
                    response_column,
                    _response_toxicity_pipeline,
                    _response_toxicity_tokenizer,
                )
            )
        )
        _registered[schema_name].add(f"{response_column}.toxicity")
