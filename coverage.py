from argparse import ArgumentParser
from bs4 import BeautifulSoup
from collections import defaultdict
from hashlib import sha1
from json import dump, loads
from pathlib import Path
import re


def git_blob_hash(file):
    with Path(file).open() as f:
        data = f.read()

    if isinstance(data, str):
        data = data.encode()

    data = b'blob ' + str(len(data)).encode() + b'\0' + data

    h = sha1()
    h.update(data)

    return h.hexdigest()


def template_name_and_line_map(twig_caches, verbose):
    def template_name(lines):
        for i, line in enumerate(lines):
            if line.find('function getSourceContext()') != -1:
                return lines[i + 2].split('"')[-2]

    def line_map(lines):
        for i, line in enumerate(lines):
            if line.find('function getDebugInfo()') != -1:
                line_map = lines[i + 2].split(',')
                line_map = [line_map[0].split(
                    '(')[-1].lstrip()] + [x.lstrip() for x in line_map[1:-1]]

                return [list(map(int, [y for y in x.split(' => ')]))
                        for x in line_map]

    cache_to_name_map, cache_to_line_map = {}, {}

    class_regex = re.compile('^\s*class.*$')
    twig_class_regex = re.compile(
        '^\s*class __TwigTemplate_([0-9a-f]{64}) extends Twig_Template$')

    for file in twig_caches:
        file_path = Path(file)

        if file_path.is_file():
            with file_path.open() as f:
                lines = f.readlines()

            for line in lines:
                if re.match(class_regex, line):
                    if re.match(twig_class_regex, line):
                        name = template_name(lines)
                        cache_to_name_map[
                            file] = file if name is None else name
                    else:
                        cache_to_name_map[file] = file

                    break

            if file not in cache_to_name_map:
                cache_to_name_map[file] = file

            if file in cache_to_name_map and cache_to_name_map[file] != file:
                if verbose:
                    print('Mapping cache file {} to template {}'.format(
                        file, cache_to_name_map[file]))

                cache_to_line_map[file] = line_map(lines)

    return (cache_to_name_map, cache_to_line_map)


def process_xml(source_xml, verbose):
    xml_obj = BeautifulSoup(source_xml, features='xml')

    files, temp_coverage = [], {}

    for file in xml_obj.find_all('file', recursive=True):
        name = file.attrs['name']
        files.append(name)

        lines = file.find_all('line', recursive=True)

        if lines:
            coverage = [-1] * int(lines[-1].attrs['num'])

            for line in lines:
                attr = line.attrs
                num, count = int(attr['num']), int(attr['count'])

                coverage[num - 1] = count

            temp_coverage[name] = coverage

    files_coverage = {}
    cache_to_name_map, cache_to_line_map = template_name_and_line_map(
        files, verbose)

    for temp_name in temp_coverage:
        name, temp_cov = cache_to_name_map[temp_name], temp_coverage[temp_name]

        if temp_name != name:
            coverage = [-1] * cache_to_line_map[temp_name][0][1]

            for x, y in cache_to_line_map[temp_name]:
                coverage[y - 1] = temp_cov[x - 1]

            temp_cov = coverage

        files_coverage[name] = {
            'coverage': temp_cov
        }

    return files_coverage


def coverage_report(coverage_dict, repo, verbose):
    coverage_json = {
        'covered_percent': 0,
        'covered_strength': 0,
        'line_counts': {},
        'source_files': []
    }

    coverage_total, coverage_covered, coverage_strength, coverage_missed = 0, 0, 0, 0

    for file in coverage_dict:
        blob_id = coverage_dict[file]['blob_id'] if (
            'blob_id' in coverage_dict[file]) else git_blob_hash(file)

        source_file = {
            'blob_id': blob_id,
            'coverage': '[' + ','.join(['null' if val == -1 else str(val) for val in coverage_dict[file]['coverage']]) + ']'
        }

        if verbose:
            print('Processing file {} (blob_id: {})'.format(file, blob_id))

        total, covered, strength, missed = 0, 0, 0, 0

        for val in coverage_dict[file]['coverage']:
            if val == -1:
                continue

            if not val:
                missed += 1
                coverage_missed += 1
            else:
                covered += 1
                coverage_covered += 1

            total += 1
            coverage_total += 1

            strength += val
            coverage_strength += val

        source_file['covered_percent'] = (covered / total) * 100
        source_file['covered_strength'] = strength / total

        source_file['line_counts'] = {
            'total': total,
            'missed': missed,
            'covered': covered
        }

        file_path = file.split('/')
        if repo in file_path:
            pos = file_path.index(repo)

            if pos != len(file_path) - 1:
                source_file['name'] = '/'.join(file_path[pos + 1:])
            else:
                source_file['name'] = file
        else:
            source_file['name'] = file

        coverage_json['source_files'].append(source_file)

    coverage_json['covered_percent'] = (
        coverage_covered / coverage_total) * 100
    coverage_json['covered_strength'] = coverage_strength / coverage_total

    coverage_json['line_counts'] = {
        'total': coverage_total,
        'missed': coverage_missed,
        'covered': coverage_covered
    }

    return coverage_json


def write_coverage(coverage_json, output_file):
    output_file_path = Path(output_file)

    if output_file_path.name != output_file:
        output_file_path_parts = output_file_path.parts
        is_absolute = output_file_path_parts[0] == '/'

        output_file_dir = '/'.join(output_file_path_parts[
                                   1 if is_absolute else 0:-1])
        output_file_dir = ('/' if is_absolute else './') + output_file_dir

        if not output_file_path.exists():
            print('Creating directory {}'.format(output_file_dir))
            Path(output_file_dir).mkdir(parents=True, exist_ok=True)

    print('Writing JSON report to file {}'.format(output_file))

    with open(output_file, 'w') as f:
        dump(coverage_json, f, indent=4)


def process(file, output_file, repo, verbose):
    file_path = Path(file)

    if file_path.is_file():
        with file_path.open() as f:
            source_xml = f.read()

        coverage = process_xml(source_xml, verbose)
        coverage_json = coverage_report(coverage, repo, verbose)

        if verbose:
            print(coverage_json)

        write_coverage(coverage_json, output_file)
    else:
        print('File {} not found'.format(file))


def merge(reports_dir, output_file, repo, verbose):
    reports_dir = Path(reports_dir)

    if reports_dir.exists():
        reports = list(reports_dir.glob('**/*.json'))

        if len(reports) < 2:
            print('At least two JSON files required')

        if verbose:
            print('Merging {}'.format(', '.join([x.name for x in reports])))

        merged_coverage = {}

        with reports[0].open() as f:
            for file_coverage in loads(f.read())['source_files']:
                merged_coverage[file_coverage['name']] = {
                    'blob_id': file_coverage['blob_id'],
                    'coverage': [-1 if x == 'null' else int(x) for x in file_coverage['coverage'][1:-1].split(',')],
                }

        for i in range(1, len(reports)):
            with reports[i].open() as f:
                for file_coverage in loads(f.read())['source_files']:
                    blob_id = file_coverage['blob_id']
                    new_coverage = [-1 if x == 'null' else int(x) for x in file_coverage[
                        'coverage'][1:-1].split(',')]
                    name = file_coverage['name']

                    if name in merged_coverage:
                        if merged_coverage[name]['blob_id'] != blob_id:
                            continue

                        old_coverage = merged_coverage[name]['coverage']

                        len_old, len_new = len(old_coverage), len(new_coverage)

                        if len_old > len_new:
                            for _ in range(len_old - len_new):
                                new_coverage.append(-1)
                        elif len_old < len_new:
                            for _ in range(len_new - len_old):
                                old_coverage.append(-1)

                        coverage = []

                        for new, old in zip(new_coverage, old_coverage):
                            if new != -1 and old != -1:
                                coverage.append(new + old)
                            elif new == -1 and old == -1:
                                coverage.append(-1)
                            else:
                                coverage.append(new if new != -1 else old)

                        merged_coverage[name] = {
                            'blob_id': blob_id,
                            'coverage': coverage
                        }
                    else:
                        merged_coverage[name] = {
                            'blob_id': blob_id,
                            'coverage': coverage
                        }

        coverage_json = coverage_report(merged_coverage, repo, verbose)

        if verbose:
            print(coverage_json)

        write_coverage(coverage_json, output_file)
    else:
        print('Directory {} not found'.format(reports_dir))


def argument_parser():
    parser = ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("-p", "--process", metavar='clover.xml',
                        help="generate JSON report from clover xml")
    parser.add_argument("-m", "--merge", metavar='json-reports-dir',
                        help="merge multiple JSON reports")
    parser.add_argument("-r", "--repo", required=True, metavar='my-repo',
                        help="repository name to trim the path prefix")
    parser.add_argument("-o", "--output", metavar='report.json',
                        default="report.json", help="output file name")

    return parser

if __name__ == '__main__':
    parser = argument_parser()
    args = parser.parse_args()

    if not (args.process or args.merge):
        parser.error("argument -p/--process or -m/--merge required")

    if args.process and args.merge:
        parser.error(
            "arguments -p/--process and -m/--merge can not be used together")

    if args.process:
        process(args.process, args.output, args.repo, args.verbose)
    else:
        merge(args.merge, args.output, args.repo, args.verbose)
