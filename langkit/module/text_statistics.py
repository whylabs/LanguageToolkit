from functools import partial
from typing import Any, Dict, Iterator, List, Literal, Union, cast

import pandas as pd
from textstat import textstat

from langkit.module.module import ModuleType, UdfSchemaArgs
from whylogs.experimental.core.metrics.udf_metric import StandardMetric
from whylogs.experimental.core.udf_schema import (
    MetricSpec,
    ResolverSpec,
    UdfSpec,
)

TextStat = Literal[
    "flesch_kincaid_grade",
    "flesch_reading_ease",
    "smog_index",
    "coleman_liau_index",
    "automated_readability_index",
    "dale_chall_readability_score",
    "linsear_write_formula",
    "gunning_fog",
    "text_standard",
    "fernandez_huerta",
    "szigriszt_pazos",
    "gutierrez_polini",
    "crawford",
    "gulpease_index",
    "osman",
    "syllable_count",
    "lexicon_count",
    "sentence_count",
    "char_count",
    "letter_count",
    "polysyllabcount",
    "monosyllabcount",
    "difficult_words",
]


class UdfInput:
    def __init__(self, text: Union[pd.DataFrame, Dict[str, List[Any]]]) -> None:
        self.text = text

    def iter_column(self, column_name: str) -> Iterator[Any]:
        if column_name not in self.text:
            return iter([])

        if isinstance(self.text, pd.DataFrame):
            col = cast(pd.Series, self.text[column_name])
            return cast(Iterator[Any], iter(col))
        else:
            return iter(self.text[column_name])


def _textstat_module(stat: TextStat, column_name: str) -> UdfSchemaArgs:
    def _udf(column_name: str, text: Union[pd.DataFrame, Dict[str, List[Any]]]) -> Any:
        stat_func = getattr(textstat, stat)
        return [stat_func(it) for it in UdfInput(text).iter_column(column_name)]

    udf = partial(_udf, column_name)

    textstat_udf = UdfSpec(
        column_names=[column_name],
        udfs={f"{column_name}.{stat}": udf},
    )

    textstat_resolver_spec = ResolverSpec(
        f"{column_name}.{stat}",
        None,
        [
            MetricSpec(StandardMetric.counts.value),
            MetricSpec(StandardMetric.types.value),
            MetricSpec(StandardMetric.distribution.value),
        ],
    )

    schema = UdfSchemaArgs(
        types={column_name: str},
        resolvers=[textstat_resolver_spec],
        udf_specs=[textstat_udf],
    )

    return schema


__reading_ease_module = partial(_textstat_module, "flesch_reading_ease")
prompt_reading_ease_module = partial(__reading_ease_module, column_name="prompt")
response_reading_ease_module = partial(__reading_ease_module, column_name="response")
prompt_response_reading_ease_module = [prompt_reading_ease_module, response_reading_ease_module]


__flesch_kincaid_grade_level_module = partial(_textstat_module, "flesch_kincaid_grade")
prompt_flesch_kincaid_grade_level_module = partial(__flesch_kincaid_grade_level_module, column_name="prompt")
response_flesch_kincaid_grade_level_module = partial(__flesch_kincaid_grade_level_module, column_name="response")
prompt_response_flesch_kincaid_grade_level_module = [
    prompt_flesch_kincaid_grade_level_module,
    response_flesch_kincaid_grade_level_module,
]


__char_count_module = partial(_textstat_module, "char_count")
prompt_char_count_module = partial(__char_count_module, column_name="prompt")
response_char_count_module = partial(__char_count_module, column_name="response")
prompt_response_char_count_module = [prompt_char_count_module, response_char_count_module]


__syllable_count_module = partial(_textstat_module, "syllable_count")
prompt_syllable_count_module = partial(__syllable_count_module, column_name="prompt")
response_syllable_count_module = partial(__syllable_count_module, column_name="response")
prompt_response_syllable_count_module = [prompt_syllable_count_module, response_syllable_count_module]


__lexicon_count_module = partial(_textstat_module, "lexicon_count")
prompt_lexicon_count_module = partial(__lexicon_count_module, column_name="prompt")
response_lexicon_count_module = partial(__lexicon_count_module, column_name="response")
prompt_response_lexicon_count_module = [prompt_lexicon_count_module, response_lexicon_count_module]


__sentence_count_module = partial(_textstat_module, "sentence_count")
prompt_sentence_count_module = partial(__sentence_count_module, column_name="prompt")
response_sentence_count_module = partial(__sentence_count_module, column_name="response")
prompt_response_sentence_count_module = [prompt_sentence_count_module, response_sentence_count_module]


__letter_count_module = partial(_textstat_module, "letter_count")
prompt_letter_count_module = partial(__letter_count_module, column_name="prompt")
response_letter_count_module = partial(__letter_count_module, column_name="response")
prompt_response_letter_count_module = [prompt_letter_count_module, response_letter_count_module]


__polysyllabcount_module = partial(_textstat_module, "polysyllabcount")
prompt_polysyllabcount_module = partial(__polysyllabcount_module, column_name="prompt")
response_polysyllabcount_module = partial(__polysyllabcount_module, column_name="response")
prompt_response_polysyllabcount_module = [prompt_polysyllabcount_module, response_polysyllabcount_module]


__monosyllabcount_module = partial(_textstat_module, "monosyllabcount")
prompt_monosyllabcount_module = partial(__monosyllabcount_module, column_name="prompt")
response_monosyllabcount_module = partial(__monosyllabcount_module, column_name="response")
prompt_response_monosyllabcount_module = [prompt_monosyllabcount_module, response_monosyllabcount_module]


__difficult_words_module = partial(_textstat_module, "difficult_words")
prompt_difficult_words_module = partial(__difficult_words_module, column_name="prompt")
response_difficult_words_module = partial(__difficult_words_module, column_name="response")
prompt_response_difficult_words_module = [prompt_difficult_words_module, response_difficult_words_module]


prompt_response_textstat_module: ModuleType = [
    *prompt_response_reading_ease_module,
    *prompt_response_flesch_kincaid_grade_level_module,
    *prompt_response_char_count_module,
    *prompt_response_syllable_count_module,
    *prompt_response_lexicon_count_module,
    *prompt_response_sentence_count_module,
    *prompt_response_letter_count_module,
    *prompt_response_polysyllabcount_module,
    *prompt_response_monosyllabcount_module,
    *prompt_response_difficult_words_module,
]

prompt_textstat_module: ModuleType = [
    prompt_reading_ease_module,
    prompt_flesch_kincaid_grade_level_module,
    prompt_char_count_module,
    prompt_syllable_count_module,
    prompt_lexicon_count_module,
    prompt_sentence_count_module,
    prompt_letter_count_module,
    prompt_polysyllabcount_module,
    prompt_monosyllabcount_module,
    prompt_difficult_words_module,
]

response_textstat_module: ModuleType = [
    response_reading_ease_module,
    response_flesch_kincaid_grade_level_module,
    response_char_count_module,
    response_syllable_count_module,
    response_lexicon_count_module,
    response_sentence_count_module,
    response_letter_count_module,
    response_polysyllabcount_module,
    response_monosyllabcount_module,
    response_difficult_words_module,
]
