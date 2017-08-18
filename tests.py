import io
import os
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


def test_atomic_write(tmpdir):
    path = str(tmpdir.join('file'))
    contemplate.atomic_write(path, 'hi')
    assert open(path).read() == 'hi'
    assert not os.path.exists(path + '.contemplate.tmp')


def test_atomic_write_rename_fails(tmpdir, monkeypatch):

    class TestException(Exception):
        pass

    def rename(x, y):
        raise TestException()

    monkeypatch.setattr(os, 'rename', rename)
    path = str(tmpdir.join('file'))
    with pytest.raises(TestException):
        contemplate.atomic_write(path, 'hi')
    assert not os.path.exists(path + '.contemplate.tmp')


def render_testcases():
    def envfile():
        return io.StringIO("TEST=envfile")

    env = {'TEST': 'env'}

    yield {}, None, {}, "'' ''"
    yield {'test': 'ctx'}, None, {}, "'ctx' ''"

    # test env settings
    yield {}, None, env, "'' 'env'"
    yield {}, envfile(), {}, "'' 'envfile'"
    yield {}, envfile(), env, "'' 'envfile'"
    yield {'env': {'TEST': 'ctx'}}, envfile(), env, "'' 'ctx'"


@pytest.mark.parametrize('context,envfile,env,expected', render_testcases())
def test_render(context, envfile, env, expected):
    template = "'{{ test }}' '{{ env['TEST'] }}'"
    output = contemplate.render(template, context, envfile, env)
    assert output == expected + '\n'
