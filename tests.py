import io
import os
import textwrap

import pytest
import reify


def test_parse_envfile():
    envfile = io.StringIO(textwrap.dedent("""
        X=x
        Y=y$X  # substitution within file
        Z=z$Z  # base env substitution
        quotes="some value"  # test quoted values
        quotes_single='some value'  # test quoted values
        # line level comment, then a blank line

    """))
    env = {'Z': 'z'}
    reify.parse_envfile(env, envfile)
    assert env == {
        'X': 'x',
        'Y': 'yx',
        'Z': 'zz',
        'quotes': 'some value',
        'quotes_single': 'some value',
    }


def test_parse_envfile_error():
    envfile = io.StringIO("X=x\nY=y foo")
    env = {}
    with pytest.raises(Exception) as e:
        reify.parse_envfile(env, envfile)
        assert 'X=x y' in str(e)
        assert 'line 2' in str(e)


def test_parse_yamlfile():
    assert reify.parse_yamlfile(io.StringIO("")) == {}
    assert reify.parse_yamlfile(io.StringIO("{}")) == {}
    assert reify.parse_yamlfile(io.StringIO("[]")) == {}

    non_dict = io.StringIO("[1]")
    non_dict.name = 'test'
    with pytest.raises(Exception):
        reify.parse_yamlfile(non_dict)

    d = reify.parse_yamlfile(io.StringIO(textwrap.dedent("""
        foo:
            bar:
                - 1
                - 2
    """)))
    assert d == {'foo': {'bar': [1, 2]}}


def test_atomic_write(tmpdir):
    path = str(tmpdir.join('file'))
    reify.atomic_write(path, 'hi')
    assert open(path).read() == 'hi'
    assert not os.path.exists(path + '.reify.tmp')


def test_atomic_write_rename_fails(tmpdir, monkeypatch):

    class TestException(Exception):
        pass

    def rename(x, y):
        raise TestException()

    monkeypatch.setattr(os, 'rename', rename)
    path = str(tmpdir.join('file'))
    with open(path, 'w') as f:
        f.write('other')
    with pytest.raises(TestException):
        reify.atomic_write(path, 'hi')
    assert not os.path.exists(path + '.reify.tmp')
    assert open(path).read() == 'other'


TEMPLATE = "'{{ test }}' '{{ env['TEST'] }}'"


def test_render_none():
    output = reify.render(TEMPLATE, {}, None, {})
    assert output == "'' ''\n"


def test_render_simple():
    output = reify.render(TEMPLATE, {'test': 'ctx'}, None, {})
    assert output == "'ctx' ''\n"


def test_render_envvar():
    output = reify.render(TEMPLATE, {}, None, {'TEST': 'env'})
    assert output == "'' 'env'\n"


def test_render_envfile():
    output = reify.render(TEMPLATE, {}, io.StringIO('TEST=envfile'), {})
    assert output == "'' 'envfile'\n"


def test_render_envfile_overrides_env():
    output = reify.render(
        TEMPLATE, {}, io.StringIO('TEST=envfile'), {'TEST': 'env'})
    assert output == "'' 'envfile'\n"


def test_render_ctx_overrides_envfile():
    output = reify.render(
        TEMPLATE, {'env': {'TEST': 'ctx'}}, io.StringIO('TEST=envfile'), {})
    assert output == "'' 'ctx'\n"
