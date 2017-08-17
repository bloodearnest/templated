import argparse
import contextlib
import os
import select
import string
import sys

import yaml
import jinja2


def have_stdin():
    return select.select([sys.stdin, ], [], [], 0.0)[0]


def parse_envfile(env, envfile):
    for line in envfile:
        line = line.strip()
        if not line:
            continue
        var, _, comment = line.partition('#')
        if not var:
            continue
        rendered = string.Template(var.strip()).substitute(env)
        left, _, right = rendered.partition('=')
        env[left] = right


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
        default=sys.stdout,
        help='output file',
    )

    return parser


def write(template, context, output, envfile=None):
    """Render a template with context to output.

    template is a string containing the template.
    """
    tmpl = jinja2.Template(template)

    ctx = {'env': os.environ.copy()}
    if envfile:
        parse_envfile(ctx['env'], envfile)
    ctx.update(context)
    content = tmpl.render(ctx) + '\n'

    if output in (sys.stdout, sys.stderr):
        output.write(content)
    else:
        temp = output + '.contemplate.tmp'
        try:
            with open(temp, 'w') as f:
                f.write(content)
            os.rename(temp, output)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.remove(temp)


def main():
    parser = get_parser()
    args = parser.parse_args()

    context = {}

    if have_stdin():
        context.update(parse_yamlfile(sys.stdin))

    if args.context:
        context.update(parse_yamlfile(args.context))

    context.update(args.extra)

    if args.output == '-':
        args.output = sys.stdout

    write(args.template.read(), context, args.output, args.envfile)


if __name__ == '__main__':
    main()
