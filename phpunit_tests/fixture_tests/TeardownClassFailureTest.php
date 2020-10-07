<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class TeardownClassFailureTest extends TestCase
{

    public static function tearDownAfterClass(): void
    {
        $this->assertTrue(false);

    }

    public function testTrueFalse(): void
    {
        $this->assertTrue(false);
    }

}
