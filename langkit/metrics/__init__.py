import pandas as pd

from langkit.metrics.metric import EvaluationConfifBuilder, EvaluationResult, Metric, MetricConfig, UdfInput
from langkit.metrics.text_statistics import (
    TextStat,
    prompt_reading_ease_module,
    prompt_textstat_module,
    response_reading_ease_module,
    response_textstat_module,
    textstat_module,
)


# This would mostly be a manual repackaging of the various metrics in this module to make it nicer and discoverable
class lib:
    class text_stat:
        @staticmethod
        def custom(stat: TextStat, prompt_or_response: str) -> Metric:
            return lambda: textstat_module(stat, prompt_or_response)

        class char_count:
            @staticmethod
            def prompt() -> Metric:
                return prompt_textstat_module

            @staticmethod
            def response() -> Metric:
                return response_textstat_module

        class reading_ease:
            @staticmethod
            def prompt() -> Metric:
                return prompt_reading_ease_module

            @staticmethod
            def response() -> Metric:
                return response_reading_ease_module

            @staticmethod
            def custom(prompt_or_response_name: str) -> Metric:
                return lambda: textstat_module("flesch_reading_ease", prompt_or_response_name)


# Examples
crawford = lib.text_stat.custom("crawford", "prompt")
weird_prompt_name = lib.text_stat.reading_ease.custom("weird_prompt_name")
reading_ease_prompt = lib.text_stat.reading_ease.prompt()


def custom_prompt_metric() -> MetricConfig:
    def evaluate(df: pd.DataFrame) -> EvaluationResult:
        metrics = [len(it) for it in UdfInput(df).iter_column_rows("prompt") if isinstance(it, str)]
        return EvaluationResult(metrics)

    return MetricConfig(name="custom_metric", input_name="prompt", evaluate=evaluate)


my_metric_configs = (
    EvaluationConfifBuilder().add(crawford).add(weird_prompt_name).add(reading_ease_prompt).add(custom_prompt_metric).build()
)

## And eventually we evaluate it in a pipeline
# pipeline.evaluate(df, my_metric_configs)
## Or maybe we create the pipeline with it
# pipeline = Pipeline(my_metric_configs)
