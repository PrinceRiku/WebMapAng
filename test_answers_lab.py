import pytest

from answers_lab import selection_sort


def test_selection_sort_none_array_raises_type_error():
    """None is not a sortable array and should be rejected clearly."""
    with pytest.raises(TypeError):
        selection_sort(None)


def test_selection_sort_decimal_array():
    values = [3.14, -1.5, 2.718, 0.0, 1.25]

    assert selection_sort(values) == [-1.5, 0.0, 1.25, 2.718, 3.14]
    assert values == [3.14, -1.5, 2.718, 0.0, 1.25]


def test_selection_sort_repeated_values_array():
    values = [4, 2, 4, 1, 2, 1, 4]

    assert selection_sort(values) == [1, 1, 2, 2, 4, 4, 4]
    assert values == [4, 2, 4, 1, 2, 1, 4]
