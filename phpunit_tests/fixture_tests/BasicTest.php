<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class BasicTest extends TestCase
{
    public function testTrueFalse(): void
    {
        sleep(3);

        $this->assertTrue(false);
    }
}
