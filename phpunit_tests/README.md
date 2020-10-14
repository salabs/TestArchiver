# Phpunit fixture tests

These are fixture tests designed to produce test inputs for the php-junit parser using the Phpunit testing library.

The examples here can also be used as example for using TestArchiver with phpunit

## Required modules

[phpunit](https://phpunit.readthedocs.io/en/9.3/index.html)

The Phpunit package can be either downloaded as a phar or installed through composer.


```
➜ wget -O phpunit https://phar.phpunit.de/phpunit-7.phar

➜ chmod +x phpunit

➜ ./phpunit --version
```

The phpunit executable can then be moved to /usr/local/bin if you want it in path.

To install with composer

```
➜ composer require --dev phpunit/phpunit ^7

➜ ./vendor/bin/phpunit --version
```

[Options for phpunit, contains logging](https://phpunit.readthedocs.io/en/9.3/textui.html)


## Runing tests and producing xml report

```
phpunit --log-junit output.xml fixture_tests
```

As Phpunit does not contain a timestamp for the time of test execution it is added with the parser, thus the timestamp in epimetheus for example refers to the time of testarchiver execution.
