import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { unattemptedSnapshot } from './photo-batch-worker.mjs';

const hash = text => createHash('sha256').update(text).digest('hex');
test('redescoberta preserva IDs novos e não repete os já tentados', () => {
  const attempted = new Set();
  const first = '100\n200\n';
  const queue = unattemptedSnapshot(first, hash(first), 2, attempted);
  queue.forEach(id => attempted.add(id));
  const second = '200\n300\n'; // 100 ganhou foto, 200 segue 404, 300 chegou depois.
  assert.deepEqual(unattemptedSnapshot(second, hash(second), 2, attempted), ['300']);
  attempted.add('300');
  assert.deepEqual(unattemptedSnapshot(second, hash(second), 2, attempted), []);
  assert.deepEqual(unattemptedSnapshot(second, hash(second), 2, new Set()), ['200', '300']);
});
test('fotografia adulterada ou duplicada não produz fila', () => {
  assert.throws(() => unattemptedSnapshot('100\n', hash('200\n'), 1, new Set()));
  assert.throws(() => unattemptedSnapshot('100\n100\n', hash('100\n100\n'), 2, new Set()));
  assert.throws(() => unattemptedSnapshot('100\n', hash('100\n'), 2, new Set()));
});
