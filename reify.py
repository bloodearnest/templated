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
    return select.select([sys.stdin, ], [], [], 0.0)[0]


def parse_envfile(env, envfile):
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
    ctx = yaml.safe_load(stream)
    if not ctx:
        return {}
    if isinstance(ctx, dict):
        return ctx
    raise Exception('could not load dict from yaml in {}'.format(stream.name))


def extra(raw_arg):
    if '=' not in raw_arg:
        raise argparse.ArgumentTypeError('extra config must be key=value')
    return raw_arg.split('=', 1)


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
        help='output file, defaults to stdout',
    )

    return parser


def atomic_write(path, content):
    temp = path + '.contemplate.tmp'
    try:
        with open(temp, 'w') as f:
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


def contemplate(output, template, context, envfile=None, env=os.environ):
    atomic_write(output, render(template, context, envfile, env))


def main():
    parser = get_parser()
    args = parser.parse_args()

    context = {}

    if have_stdin():
        context.update(parse_yamlfile(sys.stdin))

    if args.context:
        context.update(parse_yamlfile(args.context))

    context.update(args.extra)

    content = render(args.template.read(), context, args.envfile)
    if args.output == '-':
        sys.stdout.write(content)
    else:
        atomic_write(args.output, content)


if __name__ == '__main__':
    main()
