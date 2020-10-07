<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class SkippingTest extends TestCase
{
    public function testTrueFalse(): void
    {
        $this->assertTrue(false);
    }
    /**
     * @requires OSFAMILY Windows
     */
    public function testSkip(): void
    {
        $this->assertTrue(true);
    }
}
