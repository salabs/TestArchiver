<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class SetupClassFailureTest extends TestCase
{
    
    public static function setUpBeforeClass(): void
    {
        $this->assertTrue(true);
    }

    public function testTrueFalse(): void
    {
        $this->assertTrue(true);
    }
}
