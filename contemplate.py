import argparse
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
        if line[0] == '#':
            continue
        line = string.Template(line.strip()).substitute(env)
        left, _, right = line.partition('=')
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
        help='file to load context data from',
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


def main():
    parser = get_parser()
    args = parser.parse_args()

    template = jinja2.Template(args.template.read())
    context = {'env': os.environ.copy()}

    if args.envfile:
        parse_envfile(context['env'], args.envfile)

    if have_stdin():
        context.update(parse_yamlfile(sys.stdin))

    if args.context:
        context.update(parse_yamlfile(args.context))

    context.update(args.extra)
    content = template.render(context) + '\n'

    if args.output == '-':
        args.output = sys.stdout

    if args.output in (sys.stdout, sys.stderr):
        args.output.write(content)
    else:
        temp = args.output + '.tmp'
        try:
            with open(temp, 'w') as f:
                f.write(content)
            os.rename(temp, args.output)
        finally:
            try:
                os.remove(temp)
            except FileNotFoundError:
                pass


if __name__ == '__main__':
    main()
