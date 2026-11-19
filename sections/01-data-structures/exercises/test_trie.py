from trie import Trie


def make():
    t = Trie()
    for w in ["car", "card", "care", "cart", "cat", "dog", "do"]:
        t.insert(w)
    return t


def test_contains_exact_only():
    t = make()
    assert t.contains("car")
    assert t.contains("do")
    assert not t.contains("ca")
    assert not t.contains("cards")


def test_starts_with():
    t = make()
    assert t.starts_with("ca")
    assert t.starts_with("")
    assert not t.starts_with("x")


def test_words_with_prefix_sorted():
    t = make()
    assert t.words_with_prefix("car") == ["car", "card", "care", "cart"]
    assert t.words_with_prefix("d") == ["do", "dog"]
    assert t.words_with_prefix("z") == []


def test_limit_and_duplicates():
    t = make()
    t.insert("car")
    assert t.words_with_prefix("ca", limit=2) == ["car", "card"]
