<?php declare(strict_types=1);
use PHPUnit\Framework\TestCase;

class DependenciesTest extends TestCase
{

    public function testFail(): void
    {
        $this->assertTrue(false);
    }

    public function testPass(): void
    {
        $this->assertTrue(true);
    }

    public function testPassWithParam(): string
    {
        $this->assertTrue(true);
        return 'first';
    }
    /**
    * @depends testPass
    */
    public function testDependencyWithPass(): void
    {
        $this->assertTrue(true);
    }

    /**
    * @depends testFail
    */
    public function testDependencyWithFail(): void
    {
        $this->assertTrue(true);
    }

    /**
     * @depends testPassWithParam
     */
    public function testDependencyVariableWithPass($first): void
    {
        $this->assertSame('first', $first);
    }

    public function failingAdditionsData(): array
    {
        return [
            [0, 0, 0],
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 3]
        ];
    }

    public function passingAdditionData(): array
    {
        return [
            [0, 0, 0],
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 2]
        ];
    }

    /**
     * @dataProvider failingAdditionsData
     */
    public function testDatadependencyWithFail(): void
    {
        $this->assertSame($expected, $a + $b);
    }

    /**
     * @dataProvider passingAdditionData
     */
    public function testDatadependencyWithPass(): void
    {
        $this->assertSame($expected, $a + $b);
    }
}
