import argparse
import contextlib
import os
import select
import shlex
import string
import sys

import yaml
import jinja2


def have_stdin():
    """Do we have input ready to read on stdin?"""
    return select.select([sys.stdin, ], [], [], 0.0)[0]


def parse_envfile(env, envfile):
    """Parse an env file into the supplied environment dict.

    An env file is a list of assignments to env vars that can be sourced or
    used as a systemd unit EnvironmentFile.  Parsing is done via shlex, leading
    or trailing comments are handled.  Additionally, simple $ substitution is
    performed on the RHS value.
    """
    for i, line in enumerate(envfile, 1):
        line = line.strip()
        if not line:
            continue
        var, _, comment = line.partition('#')
        var = var.strip()
        if not var:
            continue
        parts = shlex.split(var)
        if len(parts) > 1:
            raise Exception('cannot parse envfile line {}: {}'.format(i, line))
        left, _, right = parts[0].partition('=')
        rendered = string.Template(right).substitute(env)
        env[left] = rendered


def parse_yamlfile(stream):
    """Parse a yaml file, returning empty dict on empty files."""
    ctx = yaml.safe_load(stream)
    if not ctx:
        return {}
    if isinstance(ctx, dict):
        return ctx
    raise Exception('could not load dict from yaml in {}'.format(stream.name))


def parse_charm_defaults(stream):
    """Parse default arguments from a charm config.yaml."""
    config = yaml.safe_load(stream)
    if not config:
        return {}
    options = config.get('options', {})
    context = {}
    for name, cfg in options.items():
        t = cfg['type']
        default = cfg.get('default')
        if default is None:
            value = None
        elif t == 'string':
            value = str(default)
        elif t == 'int':
            value = int(default)
        elif t == 'float':
            value = float(default)
        elif t == 'boolean':
            value = bool(default)
        else:
            raise Exception('unknown config type: ' + t)

        context[name] = value

    return context


def extra(raw_arg):
    """argparse argument type for key=value arguments."""
    if '=' not in raw_arg:
        raise argparse.ArgumentTypeError('extra config must be key=value')
    return raw_arg.split('=', 1)


def octal_mode(raw_arg):
    """argparse argument type for modes."""
    try:
        return int(raw_arg, 8)
    except ValueError:
        raise argparse.ArgumentTypeError(
            '"{}" is not an octal mode'.format(raw_arg))


def get_parser():
    parser = argparse.ArgumentParser(description='render a jinja2 template')
    parser.add_argument(
        'template',
        type=argparse.FileType('r'),
        help='the template file',
    )
    parser.add_argument(
        'extra',
        nargs='*',
        type=extra,
        help='extra key value pairs (foo=bar)',
    )
    parser.add_argument(
        '--context', '-c',
        type=argparse.FileType('r'),
        help='file to load context data from. Can also be read from stdin.',
    )
    parser.add_argument(
        '--envfile', '-e',
        type=argparse.FileType('r'),
        help='file with environment varibles',
    )
    parser.add_argument(
        '--output', '-o',
        default='-',
        help='output file; defaults to stdout',
    )
    parser.add_argument(
        '--mode', '-m',
        type=octal_mode,
        help='mode of output file, if not stdout; defaults to 0666 - umask',
    )
    parser.add_argument(
        '--charm-config',
        type=argparse.FileType('r'),
        help='charm config file, default values will be added to template '
             'context',
    )

    return parser


def atomic_write(path, content, mode=None):
    """Attempt at atomic writes.

    For some value of atomic...
    """
    temp = path + '.reify.tmp'  # path must be on same fs for atomic rename
    try:
        with open(temp, 'w') as f:
            if mode is not None:
                os.fchmod(f.fileno(), mode)
            f.write(content)
        os.rename(temp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.remove(temp)


def render(template, context, envfile=None, env=os.environ):
    """Render a template with context to output.

    template is a string containing the template.
    """
    tmpl = jinja2.Template(template)
    ctx = {'env': env.copy()}
    if envfile:
        parse_envfile(ctx['env'], envfile)
    ctx.update(context)
    return tmpl.render(ctx) + '\n'


def reify(output, template, context, envfile=None, env=os.environ, mode=None):
    atomic_write(output, render(template, context, envfile, env), mode=mode)


def main():
    parser = get_parser()
    args = parser.parse_args()

    context = {}

    if args.charm_config:
        context.update(parse_charm_defaults(args.charm_config))

    if have_stdin():
        context.update(parse_yamlfile(sys.stdin))

    if args.context:
        context.update(parse_yamlfile(args.context))

    context.update(args.extra)

    content = render(args.template.read(), context, envfile=args.envfile)
    if args.output == '-':
        sys.stdout.write(content)
    else:
        atomic_write(args.output, content, mode=args.mode)


if __name__ == '__main__':
    main()
