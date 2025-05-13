import pytest
from palindrome_parametrized import is_palindrome

@pytest.mark.parametrize("word,expected",
                         [
                             ("madam",True),
                             ("python",False),
                             ("car",False),
                             ("level",True)
                             

                         ])

def test_is_palindrome(word, expected):
    assert is_palindrome(word) == expected