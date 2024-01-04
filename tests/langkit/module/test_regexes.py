import json
import math
import os
import tempfile
from typing import Any

import pandas as pd
import regex as re

import whylogs as why
from langkit.module.module import SchemaBuilder
from langkit.module.regexes.regex_loader import CompiledPatternGroups, PatternGroups
from langkit.module.regexes.regexes import (
    prompt_credit_card_number_regex,
    prompt_custom_regex_module,
    prompt_custom_regexes_frequent_items_module,
    prompt_default_regexes,
    prompt_email_address_regex,
    prompt_mailing_address_regex,
    prompt_phone_number_regex,
    prompt_response_credit_card_number_regex,
    prompt_response_default_regexes,
    prompt_response_email_address_regex,
    prompt_response_mailing_address_regex,
    prompt_response_phone_number_regex,
    prompt_response_ssn_regex,
    prompt_ssn_regex,
    response_credit_card_number_regex,
    response_custom_regex_module,
    response_default_regexes,
    response_email_address_regex,
    response_mailing_address_regex,
    response_phone_number_regex,
    response_ssn_regex,
)
from whylogs.core.metrics.metrics import FrequentItem
from whylogs.core.schema import DatasetSchema

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
    "ints/max",
    "ints/min",
]


def _log(item: Any, schema: DatasetSchema) -> pd.DataFrame:
    return why.log(item, schema=schema).view().to_pandas()  # type: ignore


def test_prompt_regex_df_ssn():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 119-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_ssn_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.ssn",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.ssn"] == 1
    assert actual["distribution/min"]["prompt.ssn"] == 0
    assert actual["types/integral"]["prompt.ssn"] == 4


def test_response_regex_df_ssn():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(response_ssn_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "response",
        "response.ssn",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["response.ssn"] == 1
    assert actual["distribution/min"]["response.ssn"] == 0
    assert actual["types/integral"]["response.ssn"] == 4


def test_prompt_response_df_ssn():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 119-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
            ],
            "response": [
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_ssn_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.ssn",
        "response",
        "response.ssn",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.ssn"] == 1
    assert actual["distribution/min"]["prompt.ssn"] == 0
    assert actual["types/integral"]["prompt.ssn"] == 4
    assert actual["distribution/max"]["response.ssn"] == 1
    assert actual["distribution/min"]["response.ssn"] == 0
    assert actual["types/integral"]["response.ssn"] == 4


def test_prompt_regex_df_email_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a email address: foo@whylabs.ai",
                "This is a email address: foo@whylabs.ai",
                "This is a email address: foo@whylabs.ai",
                "hi",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_email_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.email_address",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.email_address"] == 1
    assert actual["distribution/min"]["prompt.email_address"] == 0
    assert actual["types/integral"]["prompt.email_address"] == 4
    assert actual["types/string"]["prompt.email_address"] == 0


def test_response_regex_df_email_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my email address: foo@whylabs.ai",
                "I'm doing great, here's my email address: foo@whylabs.ai",
                "I'm doing great, here's my email address: foo@whylabs.ai",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(response_email_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "response",
        "response.email_address",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["response.email_address"] == 1
    assert actual["distribution/min"]["response.email_address"] == 0
    assert actual["types/integral"]["response.email_address"] == 4


def test_prompt_response_df_email_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a email address: foo@whylabs.ai",
                "This is a email address: foo@whylabs.ai",
                "This is a email address: foo@whylabs.ai",
                "something else",
            ],
            "response": [
                "I'm doing great, here's my email address:foo@whylabs.ai",
                "I'm doing great, here's my email address:foo@whylabs.ai",
                "I'm doing great, here's my email address:foo@whylabs.ai",
                "something else",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_email_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.email_address",
        "response",
        "response.email_address",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.email_address"] == 1
    assert actual["distribution/min"]["prompt.email_address"] == 0
    assert actual["types/integral"]["prompt.email_address"] == 4
    assert actual["distribution/max"]["response.email_address"] == 1
    assert actual["distribution/min"]["response.email_address"] == 0
    assert actual["types/integral"]["response.email_address"] == 4


def test_prompt_regex_df_phone_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a phone number: 123-456-7890",
                "This is a phone number: 123-456-7890",
                "This is a phone number: 123-456-7890",
                "This is a phone number: redacted",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_phone_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.phone_number",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.phone_number"] == 1
    assert actual["distribution/min"]["prompt.phone_number"] == 0
    assert actual["types/integral"]["prompt.phone_number"] == 4


def test_response_regex_df_phone_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(response_phone_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "response",
        "response.phone_number",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["response.phone_number"] == 1
    assert actual["distribution/min"]["response.phone_number"] == 0
    assert actual["types/integral"]["response.phone_number"] == 4


def test_prompt_response_regex_df_phone_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a phone number: 123-456-7890",
                "This is a phone number: 123-456-7890",
                "This is a phone number: 123-456-7890",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_phone_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.phone_number",
        "response",
        "response.phone_number",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.phone_number"] == 1
    assert actual["distribution/mean"]["prompt.phone_number"] == 0.75
    assert actual["distribution/min"]["prompt.phone_number"] == 0
    assert actual["types/integral"]["prompt.phone_number"] == 4
    assert actual["distribution/max"]["response.phone_number"] == 1
    assert actual["distribution/mean"]["response.phone_number"] == 0.75
    assert actual["distribution/min"]["response.phone_number"] == 0
    assert actual["types/integral"]["response.phone_number"] == 4


def test_prompt_regex_df_mailing_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "This is a mailing address: redacted",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_mailing_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.mailing_address",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.mailing_address"] == 1
    assert actual["distribution/min"]["prompt.mailing_address"] == 0
    assert actual["types/integral"]["prompt.mailing_address"] == 4


def test_response_regex_df_mailing_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(response_mailing_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "response",
        "response.mailing_address",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["response.mailing_address"] == 1
    assert actual["distribution/min"]["response.mailing_address"] == 0
    assert actual["types/integral"]["response.mailing_address"] == 4


def test_prompt_response_regex_df_mailing_address():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "This is a mailing address: 123 Main St, San Francisco, CA 94105",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, here's my mailing address: 123 Main St, San Francisco, CA 94105",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_mailing_address_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.mailing_address",
        "response",
        "response.mailing_address",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.mailing_address"] == 1
    assert actual["distribution/min"]["prompt.mailing_address"] == 0
    assert actual["types/integral"]["prompt.mailing_address"] == 4
    assert actual["distribution/max"]["response.mailing_address"] == 1
    assert actual["distribution/min"]["response.mailing_address"] == 0
    assert actual["types/integral"]["response.mailing_address"] == 4


def test_prompt_regex_df_credit_card_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a credit card number: 1234-5678-9012-3456",
                "This is a credit card number: 1234-5678-9012-3456",
                "This is a credit card number: 1234-5678-9012-3456",
                "This is a credit card number: redacted",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_credit_card_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.credit_card_number",
        "response",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.credit_card_number"] == 1
    assert actual["distribution/min"]["prompt.credit_card_number"] == 0
    assert actual["types/integral"]["prompt.credit_card_number"] == 4


def test_response_regex_df_credit_card_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(response_credit_card_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "response",
        "response.credit_card_number",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["response.credit_card_number"] == 1
    assert actual["distribution/min"]["response.credit_card_number"] == 0
    assert actual["types/integral"]["response.credit_card_number"] == 4


def test_prompt_response_regex_df_credit_card_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a credit card number: 1234-5678-9012-3456",
                "This is a credit card number: 1234-5678-9012-3456",
                "This is a credit card number: 1234-5678-9012-3456",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, here's my credit card number: 1234-5678-9012-3456",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_credit_card_number_regex).build()

    actual = _log(df, schema)
    assert list(actual.columns) == expected_metrics

    expected_columns = [
        "prompt",
        "prompt.credit_card_number",
        "response",
        "response.credit_card_number",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.credit_card_number"] == 1
    assert actual["distribution/min"]["prompt.credit_card_number"] == 0
    assert actual["types/integral"]["prompt.credit_card_number"] == 4
    assert actual["distribution/max"]["response.credit_card_number"] == 1
    assert actual["distribution/min"]["response.credit_card_number"] == 0
    assert actual["types/integral"]["response.credit_card_number"] == 4


def test_prompt_regex_df_default():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
                "This is a email address: foo@whylabs.ai",
            ],
            "response": [
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
                "I'm doing great, how about you?",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_default_regexes).build()

    actual = _log(df, schema)
    expected = [
        "frequent_items/frequent_strings",
        "type",
    ]

    assert sorted(list(actual.columns)) == sorted(expected)  # type: ignore

    expected_columns = [
        "prompt",
        "prompt.has_patterns",
        "response",
    ]

    # FI shouldn't be used for prompt/response, only the has_patterns
    assert math.isnan(actual["frequent_items/frequent_strings"]["prompt"])  # type: ignore
    assert math.isnan(actual["frequent_items/frequent_strings"]["response"])  # type: ignore

    assert actual.index.tolist() == expected_columns
    assert actual["frequent_items/frequent_strings"]["prompt.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="EMAIL_ADDRESS", est=1, upper=1, lower=1),
    ]


def test_response_regex_df_default():
    df = pd.DataFrame(
        {
            "prompt": [
                "How are you?",
                "How are you?",
                "How are you?",
                "How are you?",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my email address: foo@whylabs.ai",
            ],
        }
    )

    schema = SchemaBuilder().add(response_default_regexes).build()

    actual = _log(df, schema)
    expected = [
        "frequent_items/frequent_strings",
        "type",
    ]

    assert sorted(list(actual.columns)) == sorted(expected)  # type: ignore

    expected_columns = [
        "prompt",
        "response",
        "response.has_patterns",
    ]

    # FI shouldn't be used for prompt/response, only the has_patterns
    assert math.isnan(actual["frequent_items/frequent_strings"]["prompt"])  # type: ignore
    assert math.isnan(actual["frequent_items/frequent_strings"]["response"])  # type: ignore

    assert actual.index.tolist() == expected_columns
    assert actual["frequent_items/frequent_strings"]["response.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="EMAIL_ADDRESS", est=1, upper=1, lower=1),
        FrequentItem(value="PHONE_NUMBER", est=1, upper=1, lower=1),
    ]


def test_prompt_response_regex_df_default():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
                "This is a email address: foo@whylabs.ai",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my email address: foo@whylabs.ai",
            ],
        }
    )

    schema = SchemaBuilder().add(prompt_response_default_regexes).build()

    actual = _log(df, schema)
    expected = [
        "frequent_items/frequent_strings",
        "type",
    ]

    assert sorted(list(actual.columns)) == sorted(expected)  # type: ignore

    expected_columns = [
        "prompt",
        "prompt.has_patterns",
        "response",
        "response.has_patterns",
    ]

    # FI shouldn't be used for prompt/response, only the has_patterns
    assert math.isnan(actual["frequent_items/frequent_strings"]["prompt"])  # type: ignore
    assert math.isnan(actual["frequent_items/frequent_strings"]["response"])  # type: ignore

    assert actual.index.tolist() == expected_columns
    assert actual["frequent_items/frequent_strings"]["prompt.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="EMAIL_ADDRESS", est=1, upper=1, lower=1),
    ]
    assert actual["frequent_items/frequent_strings"]["response.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="EMAIL_ADDRESS", est=1, upper=1, lower=1),
        FrequentItem(value="PHONE_NUMBER", est=1, upper=1, lower=1),
    ]


def test_prompt_response_ssn_phone_number():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
                "This is a phone number: 123-456-7890",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my email address: foo@gmail.com",
            ],
        }
    )

    # mix and match several different ones
    schema = SchemaBuilder().add(prompt_response_ssn_regex + prompt_response_phone_number_regex + prompt_response_default_regexes).build()

    actual = _log(df, schema)
    expected_columns = [
        "prompt",
        "prompt.has_patterns",
        "prompt.phone_number",
        "prompt.ssn",
        "response",
        "response.has_patterns",
        "response.phone_number",
        "response.ssn",
    ]

    assert actual.index.tolist() == expected_columns

    assert actual["distribution/max"]["prompt.phone_number"] == 1
    assert actual["distribution/min"]["prompt.phone_number"] == 0
    assert actual["types/integral"]["prompt.phone_number"] == 4
    assert actual["distribution/max"]["prompt.ssn"] == 1
    assert actual["distribution/min"]["prompt.ssn"] == 0
    assert actual["types/integral"]["prompt.ssn"] == 4

    assert actual["distribution/max"]["response.phone_number"] == 1
    assert actual["distribution/min"]["response.phone_number"] == 0
    assert actual["types/integral"]["response.phone_number"] == 4
    assert actual["distribution/max"]["response.ssn"] == 1
    assert actual["distribution/min"]["response.ssn"] == 0
    assert actual["types/integral"]["response.ssn"] == 4

    assert actual["frequent_items/frequent_strings"]["prompt.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="PHONE_NUMBER", est=1, upper=1, lower=1),
    ]
    assert actual["frequent_items/frequent_strings"]["response.has_patterns"] == [
        FrequentItem(value="SSN", est=2, upper=2, lower=2),
        FrequentItem(value="EMAIL_ADDRESS", est=1, upper=1, lower=1),
        FrequentItem(value="PHONE_NUMBER", est=1, upper=1, lower=1),
    ]


def test_custom_regex_frequent_item():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
                "This is a phone number: 123-456-7890",
                "This is my password: password123",
            ],
            "response": [
                "I'm doing great, here's my phone number: 123-456-7890",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my ssn: 123-45-6789",
                "I'm doing great, here's my email address: foo@gmail.com",
                "Nice password!",
            ],
        }
    )

    regexes: PatternGroups = {"patterns": [{"name": "password detector", "expressions": [r"\bpassword\b"]}]}

    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        json.dump(regexes["patterns"], f)

    schema = SchemaBuilder().add(prompt_custom_regexes_frequent_items_module(f.name)).build()

    actual = _log(df, schema)

    expected_columns = [
        "prompt",
        "prompt.has_patterns",
        "response",
    ]

    assert actual.index.tolist() == expected_columns

    assert actual["frequent_items/frequent_strings"]["prompt.has_patterns"] == [
        FrequentItem(value="PASSWORD_DETECTOR", est=1, upper=1, lower=1),
    ]

    os.remove(f.name)


def test_custom_regex():
    df = pd.DataFrame(
        {
            "prompt": [
                "This is a ssn: 123-45-6789",
                "This is a ssn: 123-45-6789",
                "This is a ssn: redacted",
                "This is a phone number: 123-456-7890",
                "This is my password: password123",
            ],
            "response": [
                "foo I'm doing great, here's my phone number: 123-456-7890",
                "foo I'm doing great, here's my ssn: 123-45-6789",
                "foo I'm doing great, here's my ssn: 123-45-6789",
                "foo I'm doing great, here's my email address: foo@gmail.com",
                "Nice foo!",
            ],
        }
    )

    password_detector: CompiledPatternGroups = {
        "patterns": [
            {"name": "password detector", "expressions": [re.compile(r"\bpassword\b")]},
        ]
    }

    foo_detector: CompiledPatternGroups = {
        "patterns": [
            {"name": "foo detector", "expressions": [re.compile(r"\bfoo\b")]},
        ]
    }

    schema = SchemaBuilder().add(prompt_custom_regex_module(password_detector)).add(response_custom_regex_module(foo_detector)).build()

    actual = _log(df, schema)

    expected_columns = [
        "prompt",
        "prompt.password_detector",
        "response",
        "response.foo_detector",
    ]

    assert actual.index.tolist() == expected_columns
    assert actual["distribution/max"]["prompt.password_detector"] == 1
    assert actual["distribution/min"]["prompt.password_detector"] == 0
    assert actual["distribution/max"]["response.foo_detector"] == 1
    assert actual["distribution/min"]["response.foo_detector"] == 1
