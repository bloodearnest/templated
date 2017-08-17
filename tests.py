import io
import textwrap
import pytest
import contemplate


def test_parse_envfile():
    envfile = io.StringIO(textwrap.dedent("""
        X=x
        # line comment
        Y=y$X  # envfile substitution
        Z=z$Z  # env substitution
        # blank line

    """))
    env = {'Z': 'z'}
    contemplate.parse_envfile(env, envfile)
    assert env == {
        'X': 'x',
        'Y': 'yx',
        'Z': 'zz',
    }


def test_parse_yamlfile():
    assert contemplate.parse_yamlfile(io.StringIO("")) == {}
    assert contemplate.parse_yamlfile(io.StringIO("{}")) == {}
    assert contemplate.parse_yamlfile(io.StringIO("[]")) == {}

    non_dict = io.StringIO("[1]")
    non_dict.name = 'test'
    with pytest.raises(Exception):
        contemplate.parse_yamlfile(non_dict)

    d = contemplate.parse_yamlfile(io.StringIO(textwrap.dedent("""
        foo:
            bar:
                - 1
                - 2
    """)))
    assert d == {'foo': {'bar': [1, 2]}}
