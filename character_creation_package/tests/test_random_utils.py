from character_creation.services import random_utils


def test_roll_normal():
    """Tests that roll_normal returns a float."""
    # It's hard to test randomness, but we can check the type and that it runs.
    result = random_utils.roll_normal(mean=10.0, sd=2.0)
    assert isinstance(result, float)


def test_roll_uniform():
    """Tests that roll_uniform returns a float within the specified range."""
    min_val, max_val = 5.0, 10.0
    for _ in range(100):
        result = random_utils.roll_uniform(min_val, max_val)
        assert isinstance(result, float)
        assert min_val <= result <= max_val


def test_choice_with_non_empty_list():
    """Tests that choice returns an element from the list."""
    seq = [1, 2, 3, 4, 5]
    result = random_utils.choice(seq)
    assert result in seq


def test_choice_with_empty_list():
    """Tests that choice returns None for an empty list."""
    seq = []
    result = random_utils.choice(seq)
    assert result is None


def test_choice_with_single_element_list():
    """Tests that choice returns the only element."""
    seq = ["hello"]
    result = random_utils.choice(seq)
    assert result == "hello"
