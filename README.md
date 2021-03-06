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
`python3` and the following two packages should be installed:
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
The `patch.py` file fetches the *ci_service*, *environment*, and *git* objects by executing `.cc-test-reporter format-coverage`:
```
usage: patch.py [-h] [-e cc-test-reporter] -r my-repo [-i report.json]
                [-o codeclimate.json]

optional arguments:
  -h, --help            show this help message and exit
  -e cc-test-reporter, --exec cc-test-reporter
                        cc-test-reporter binary
  -r my-repo, --repo my-repo
                        repository name to trim the path prefix
  -i report.json, --input report.json
                        the JSON report
  -o codeclimate.json, --output codeclimate.json
                        output file name
```

You can generate the JSON report compatible with Code Climate:
```sh
python3 patch.py --exec cc-test-reporter --repo my-repo --input report.json --output codeclimate.json
```

Now, you can use `./cc-test-reporter upload-coverage` to upload the coverage report.
