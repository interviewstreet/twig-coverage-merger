# twig-coverage-merger
Map the code coverage report from twig template cache file to template itself

## Enable Twig Template Cache
```php
new Twig_Environment(
    new Twig_Loader_Filesystem('twig-templates-dir'),
    array(
        'cache' => 'twig-template-cache-dir'
    )
);
```

## Add Twig Template Cache to Coverage
```xml
<filter>
    <whitelist processUncoveredFilesFromWhitelist="true">
        <directory suffix=".php">twig-template-cache-dir</directory>
    </whitelist>
</filter>
```

## Generate Clover Coverage
```xml
<logging>
    <log type="coverage-clover" target="clover.xml"/>
</logging>
```

## Dependency
The `coverage.py` file requires python3. The following two packages should be installed:
```sh
sudo pip3 install bs4
CFLAGS="-O0" sudo pip3 install lxml
```

## Generate Coverage JSON
The `coverage.py` file generates the report:
```
usage: coverage.py [-h] [-v] [-p clover.xml] [-m json-reports-dir] -r my-repo
                   [-o report.json]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -p clover.xml, --process clover.xml
                        generate JSON report from clover xml
  -m json-reports-dir, --merge json-reports-dir
                        merge multiple JSON reports
  -r my-repo, --repo my-repo
                        repository name to trim the path prefix
  -o report.json, --output report.json
                        output file name
```

You can either process one XML report or merge multiple JSON reports:
```sh
python3 coverage.py --process clover.xml --repo my-repo --output report.json
python3 coverage.py --merge json-reports-dir --repo my-repo --output merged.json
```

## Upload Coverage to Code Climate
The JSON report is compatible with Code Climate, so you can use `./cc-test-reporter upload-coverage` to send the coverage report. The JSON includes the following additional sufficient information:

```json
ci_service = {
    "branch": "my-branch",
    "commit_sha": "123c1d47624ee7475b93728ea8e30c8bf1d0ef8d",
    "committed_at": 1521936646
}
```
```json
environment = {
    "pwd": "a/b/c/d/my-repo/e/g",
    "prefix": "a/b/c/d/my-repo"
}
```
```json
git = {
    "branch": "my-branch",
    "head": "123c1d47624ee7475b93728ea8e30c8bf1d0ef8d",
    "committed_at": 1521936646
}
```
