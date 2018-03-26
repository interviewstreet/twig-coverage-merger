from argparse import ArgumentParser
from json import dump, loads
from pathlib import Path
import shutil
import subprocess


def exec_cmd(cmd):
    print(cmd)

    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    if error is not None:
        print('Error executing {}'.format(cmd))

        return error

    return output.strip().decode('ascii')


def ci_env_git_info(repo):
    current_dir = Path.cwd().parts
    is_absolute = current_dir[0] == '/'

    if repo not in current_dir:
        print('Make sure to run the command inside the git directory')

        return {}, {}, {}

    prefix_dir = ('/' if is_absolute else './') + \
        '/'.join(current_dir[1 if is_absolute else 0:current_dir.index(repo) + 1])

    pwd = ('/' if is_absolute else './') + \
        '/'.join(current_dir[1 if is_absolute else 0:])

    ci_service = {
        'branch': exec_cmd(['git', 'rev-parse', '--abbrev-ref', 'HEAD']),
        'commit_sha': exec_cmd(['git', 'log', '-1', '--pretty=format:%H']),
        'committed_at': int(exec_cmd(['git', 'log', '-1', '--pretty=format:%ct']))
    }

    if ci_service['branch'] == 'HEAD':
        pull_req_sha = exec_cmd(
            ['git', 'log', '-2', '--pretty=format:%H']).split()[-1]

        ci_service['branch'] = pull_req_sha

    environment = {
        'pwd': pwd,
        'prefix': prefix_dir
    }

    git = {
        'branch': ci_service['branch'],
        'head': ci_service['commit_sha'],
        'committed_at': ci_service['committed_at']
    }

    return ci_service, environment, git


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


def apply_patch(source, patch, output_file):
    source, patch = Path(source), Path(patch)
    source_json, patch_json = {}, {}

    if source.is_file():
        with source.open() as f:
            source_json = loads(f.read())

        with patch.open() as f:
            patch_json = loads(f.read())

        source_json['ci_service'] = patch_json['ci_service']
        source_json['environment'] = patch_json['environment']
        source_json['git'] = patch_json['git']

        write_coverage(source_json, output_file)
    else:
        print('File {} not found'.format(source))

def create_patch(reporter, repo, file, output_file):
    file_path = Path(file)

    if file_path.is_file():
        current_dir = Path.cwd().parts
        is_absolute = current_dir[0] == '/'

        if repo not in current_dir:
            print('Make sure to run the command inside the git directory')

            return file

        if not (reporter.startswith('~/') or reporter.startswith('./')):
            reporter = './' + reporter

        if shutil.which(reporter) is not None:
            status = exec_cmd('chmod +x {}'.format(reporter))
            if status is not None:
                tm = exec_cmd('date +%s')
                if tm is not None:
                    tmp_xml = '/tmp/{}.txt'.format(tm)

                    with open(tmp_xml, 'w') as f:
                        f.write(
                            '<coverage><project><file name="{}"></file></project></coverage>'.format(tmp_xml))

                    coverage_patch = '/tmp/{}.json'.format(tm)
                    status = exec_cmd('{} format-coverage --input-type clover --output {} {}'.format(reporter, coverage_patch, tmp_xml))

                    if Path(coverage_patch).exists():
                        return coverage_patch
                    else:
                        print('Error')
                        print(status)

                        return None
        else:
            print('Executable {} not found'.format(reporter))
    else:
        print('File {} not found'.format(file))


def argument_parser():
    parser = ArgumentParser()

    parser.add_argument('-e', '--exec', metavar='cc-test-reporter',
                        default='cc-test-reporter', help='cc-test-reporter binary')
    parser.add_argument('-r', '--repo', required=True, metavar='my-repo',
                        help='repository name to trim the path prefix')
    parser.add_argument('-i', '--input', metavar='report.json',
                        default='report.json', help='the JSON report')
    parser.add_argument('-o', '--output', metavar='codeclimate.json',
                        default='codeclimate.json', help='output file name')

    return parser

if __name__ == '__main__':
    parser = argument_parser()
    args = parser.parse_args()

    coverage_patch = create_patch(args.exec, args.repo, args.input, args.output)
    apply_patch(args.input, coverage_patch, args.output)
