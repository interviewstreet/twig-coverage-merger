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

## Generate Coverage JSON
The `coverage.py` file generates the report:
```
  -h, --help            show this help message and exit
  -v, --verbose         increase output verbosity
  -p clover.xml, --process clover.xml
                        geneare JSON report from one clover xml
  -m coverage-dir, --merge coverage-dir
                        geneare JSON report from multiple clover xml
  -o report.json, --output report.json
                        output file name
```

You can either process one XML report or merger multiple XML reports:
```sh
python coverage.py --process clover.xml --output report.json
python coverage.py --merge coverage-dir --output report.json
```
## Upload Coverage to Code Climate
The JSON file format is compatible with Code Climate, so you can use `./cc-test-reporter upload-coverage` to send the coverage report.
