const assert = require('assert');

// Mapping example
describe('Suite', function(){
  context('Subsuite', function() {
    it('Test case', function() {});
  });
});


describe('Suite with logging', function(){
  it('Test with logging', function() {
    this.test.consoleOutputs = [ 'This is normal logging' ];
    this.test.consoleErrors = [ 'This is ERROR logging' ];
  });
});

describe('Suite with a failing test', function(){
  it('Failing test', function() {
    assert.strictEqual(1, 2);
  });
});


describe('Suite with failing setups and teardowns', function(){
  context('Suite with failing setup', function() {
    before( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });

  context('Suite with failing teardown', function() {
    after( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });

  context('Suite with both failing setup and teardown', function() {
    before( function(){
      assert.strictEqual(1, 2);
    });
    after( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });

  context('Suite with failing test setup', function() {
    beforeEach( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });

  context('Suite with failing test teardown', function() {
    afterEach( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });

  context('Suite with both failing test setup and teardown', function() {
    beforeEach( function(){
      assert.strictEqual(1, 2);
    });
    afterEach( function(){
      assert.strictEqual(1, 2);
    });
    it('Test 1', function() {});
    it('Test 2', function() {});
  });
});

