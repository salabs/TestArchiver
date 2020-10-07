<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class SetupAndTeardownTest extends TestCase
{
    protected function setUp(): void
    {
        $this->assertTrue(false);
    }

    protected function tearDown(): void
    {
        $this->assertTrue(true);
    }
    
    public function testTrueFalse(): void
    {
        $this->assertTrue(true);
    }


}
