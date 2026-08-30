import assert from "node:assert/strict";
import test from "node:test";
import {
  auditImageContent,
  assertCardId,
  deliveryUrl,
  idsFromCsv,
  parseCsv,
  parsePng,
  sourceUrl,
  uniqueCardIds
} from "../card-image-extractor.mjs";

test("card_id permanece string numerica", () => {
  assert.equal(assertCardId("17592722922839"), "17592722922839");
  assert.throws(() => assertCardId("Lionel Messi"), /card_id invalido/);
});

test("URLs sao determinadas somente pelo card_id", () => {
  assert.equal(sourceUrl("17592722922839"), "https://efimg.com/efootballhub22/images/player_cards/17592722922839_l.png");
  assert.equal(deliveryUrl("demsusjwf", "17592722922839"), "https://res.cloudinary.com/demsusjwf/image/upload/17592722922839.png");
});

test("CSV RFC4180 preserva campos com virgula e aspas", () => {
  const rows = parseCsv('id,nome,meta\r\n"101334","Nome, Um","{\"\"a\"\":1}"\r\n');
  assert.deepEqual(rows, [["id", "nome", "meta"], ["101334", "Nome, Um", '{"a":1}']]);
  assert.deepEqual(idsFromCsv('card_id,nome\n17592722922839,Messi\n'), ["17592722922839"]);
});

test("deduplicacao usa somente card_id", () => {
  assert.deepEqual(uniqueCardIds(["2", "1", "2", "01", "1"]), ["2", "1", "01"]);
});

test("valida assinatura e dimensoes PNG", () => {
  const png = Buffer.alloc(24);
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(png, 0);
  png.write("IHDR", 12, "ascii");
  png.writeUInt32BE(240, 16);
  png.writeUInt32BE(340, 20);
  assert.deepEqual(parsePng(png), { width: 240, height: 340 });
  assert.throws(() => parsePng(Buffer.from("not png")), /nao e PNG/);
});

test("auditoria de conteudo nao bloqueia arquivo nao PNG", () => {
  const audit = auditImageContent(Buffer.from("conteudo retornado pela fonte"));
  assert.equal(audit.contentAudit, "nao_png");
  assert.equal(audit.width, null);
  assert.equal(audit.height, null);
  assert.equal(audit.byteSize, 29);
  assert.match(audit.sha256, /^[0-9a-f]{64}$/);
});


