# pyright: reportUnknownMemberType=none
from functools import partial
from typing import Any

import pandas as pd

import whylogs as why
from langkit.core.metric import WorkflowMetricConfig, WorkflowMetricConfigBuilder
from langkit.core.workflow import Workflow
from langkit.metrics.library import lib
from langkit.metrics.topic import MODEL_BASE, get_custom_topic_modules, prompt_topic_module, topic_metric
from langkit.metrics.whylogs_compat import create_whylogs_udf_schema

expected_metrics = [
    "cardinality/est",
    "cardinality/lower_1",
    "cardinality/upper_1",
    "counts/inf",
    "counts/n",
    "counts/nan",
    "counts/null",
    "distribution/max",
    "distribution/mean",
    "distribution/median",
    "distribution/min",
    "distribution/n",
    "distribution/q_01",
    "distribution/q_05",
    "distribution/q_10",
    "distribution/q_25",
    "distribution/q_75",
    "distribution/q_90",
    "distribution/q_95",
    "distribution/q_99",
    "distribution/stddev",
    "type",
    "types/boolean",
    "types/fractional",
    "types/integral",
    "types/object",
    "types/string",
    "types/tensor",
]


def _log(item: Any, conf: WorkflowMetricConfig) -> pd.DataFrame:
    schema = create_whylogs_udf_schema(conf)
    return why.log(item, schema=schema).view().to_pandas()  # type: ignore


def test_topic():
    df = pd.DataFrame(
        {
            "prompt": [
                "Who is the president of the United States?",
                "What improves GDP?",
                "What causes global warming?",
                "Who was the star of the movie Titanic?",
            ],
            "response": [
                "George Washington is the president of the United States.",
                "GDP is improved by increasing the money supply.",
                "Global warming is caused by greenhouse gases.",
                "Leonardo DiCaprio was the star of the movie Titanic.",
            ],
        }
    )

    schema = WorkflowMetricConfigBuilder().add(prompt_topic_module).build()

    actual = _log(df, schema)

    expected_columns = [
        "prompt",
        "prompt.topics.economy",
        "prompt.topics.entertainment",
        "prompt.topics.medicine",
        "prompt.topics.technology",
        "response",
    ]

    assert actual.index.tolist() == expected_columns


def test_topic_base_model():
    df = pd.DataFrame(
        {
            "prompt": [
                "http://get-free-money-now.xyz/bank/details",
            ],
        }
    )

    custom_topic_module = partial(topic_metric, "prompt", ["phishing"], model_version=MODEL_BASE)
    schema = WorkflowMetricConfigBuilder().add(custom_topic_module).build()
    actual = _log(df, schema)
    assert actual.loc["prompt.topics.phishing"]["distribution/mean"] > 0.80


def test_topic_empty_input():
    df = pd.DataFrame(
        {
            "prompt": [
                "",
            ],
            "response": [
                "George Washington is the president of the United States.",
            ],
        }
    )

    schema = WorkflowMetricConfigBuilder().add(prompt_topic_module).build()

    actual = _log(df, schema)

    expected_columns = [
        "prompt",
        "prompt.topics.economy",
        "prompt.topics.entertainment",
        "prompt.topics.medicine",
        "prompt.topics.technology",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    for column in expected_columns:
        if column not in ["prompt", "response"]:
            assert actual.loc[column]["counts/null"] == 1


def test_topic_empty_input_wf():
    df = pd.DataFrame(
        {
            "prompt": [
                "",
            ],
            "response": [
                "George Washington is the president of the United States.",
            ],
        }
    )
    expected_metrics = ["prompt.topics.economy", "prompt.topics.entertainment", "prompt.topics.medicine", "prompt.topics.technology"]
    wf = Workflow(metrics=[prompt_topic_module])
    actual = wf.run(df)
    for metric_name in expected_metrics:
        assert actual.metrics[metric_name][0] is None


def test_topic_row():
    row = {
        "prompt": "Who is the president of the United States?",
        "response": "George Washington is the president of the United States.",
    }

    schema = WorkflowMetricConfigBuilder().add(prompt_topic_module).build()

    actual = _log(row, schema)

    expected_columns = [
        "prompt",
        "prompt.topics.economy",
        "prompt.topics.entertainment",
        "prompt.topics.medicine",
        "prompt.topics.technology",
        "response",
    ]

    assert actual.index.tolist() == expected_columns


def test_topic_library():
    df = pd.DataFrame(
        {
            "prompt": [
                "What's the best kind of bait?",
                "What's the best kind of punch?",
                "What's the best kind of trail?",
                "What's the best kind of swimming stroke?",
            ],
            "response": [
                "The best kind of bait is worms.",
                "The best kind of punch is a jab.",
                "The best kind of trail is a loop.",
                "The best kind of stroke is freestyle.",
            ],
        }
    )

    topics = ["fishing", "boxing", "hiking", "swimming"]
    wf = Workflow(metrics=[lib.prompt.topics(topics), lib.response.topics(topics)])
    result = wf.run(df)
    actual = result.metrics

    expected_columns = [
        "prompt.topics.fishing",
        "prompt.topics.boxing",
        "prompt.topics.hiking",
        "prompt.topics.swimming",
        "response.topics.fishing",
        "response.topics.boxing",
        "response.topics.hiking",
        "response.topics.swimming",
        "id",
    ]
    assert actual.columns.tolist() == expected_columns

    pd.set_option("display.max_columns", None)
    print(actual.transpose())

    assert actual["prompt.topics.fishing"][0] > 0.50
    assert actual["prompt.topics.boxing"][1] > 0.50
    assert actual["prompt.topics.hiking"][2] > 0.50
    assert actual["prompt.topics.swimming"][3] > 0.50

    assert actual["response.topics.fishing"][0] > 0.50
    assert actual["response.topics.boxing"][1] > 0.50
    assert actual["response.topics.hiking"][2] > 0.50
    assert actual["response.topics.swimming"][3] > 0.50


def test_custom_topic():
    df = pd.DataFrame(
        {
            "prompt": [
                "What's the best kind of bait?",
                "What's the best kind of punch?",
                "What's the best kind of trail?",
                "What's the best kind of swimming stroke?",
            ],
            "response": [
                "The best kind of bait is worms.",
                "The best kind of punch is a jab.",
                "The best kind of trail is a loop.",
                "The best kind of stroke is freestyle.",
            ],
        }
    )

    custom_topic_modules = get_custom_topic_modules(["fishing", "boxing", "hiking", "swimming"])
    schema = WorkflowMetricConfigBuilder().add(custom_topic_modules.prompt_response_topic_module).build()

    actual = _log(df, schema)

    expected_columns = [
        "prompt",
        "prompt.topics.boxing",
        "prompt.topics.fishing",
        "prompt.topics.hiking",
        "prompt.topics.swimming",
        "response",
        "response.topics.boxing",
        "response.topics.fishing",
        "response.topics.hiking",
        "response.topics.swimming",
    ]
    assert actual.index.tolist() == expected_columns
    for column in expected_columns:
        if column not in ["prompt", "response"]:
            assert actual.loc[column]["distribution/max"] >= 0.50


def test_custom_topics_base_model():
    df = pd.DataFrame(
        {
            "prompt": [
                "http://get-free-money-now.xyz/bank/details",
            ],
            "response": [
                "http://win-a-free-iphone-today.net",
            ],
        }
    )

    custom_topic_modules = get_custom_topic_modules(["phishing"], model_version=MODEL_BASE)
    schema = WorkflowMetricConfigBuilder().add(custom_topic_modules.prompt_response_topic_module).build()
    actual = _log(df, schema)
    assert actual.loc["prompt.topics.phishing"]["distribution/mean"] > 0.80
    assert actual.loc["response.topics.phishing"]["distribution/mean"] > 0.80


def test_topic_name_sanitize():
    df = pd.DataFrame(
        {
            "prompt": [
                "What's the best kind of bait?",
            ],
            "response": [
                "The best kind of bait is worms.",
            ],
        }
    )

    topics = ["Fishing supplies"]
    wf = Workflow(metrics=[lib.prompt.topics(topics), lib.response.topics(topics)])

    result = wf.run(df)
    actual = result.metrics

    expected_columns = [
        "prompt.topics.fishing_supplies",
        "response.topics.fishing_supplies",
        "id",
    ]
    assert actual.columns.tolist() == expected_columns

    pd.set_option("display.max_columns", None)
    print(actual.transpose())

    assert actual["prompt.topics.fishing_supplies"][0] > 0.50
