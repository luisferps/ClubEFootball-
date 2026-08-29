'use strict';

/**
 * Procedência física congelada para o formato legado do DT870 original.
 *
 * O PlayerBooster.bin dessa camada não usa o layout de 40 bytes do catálogo atual.
 * Estes índices foram auditados em leitura somente no mapa físico do projeto e só
 * são aceitos quando o CPK possui exatamente o fingerprint abaixo.
 */
(function installCatalogSourceMap(global) {
  const boosterDt870OriginalIndex = {
    0:160,1:142,4:1,8:132,9:3,10:164,12:150,14:5,16:158,19:7,24:9,29:11,
    32:128,33:122,34:13,39:15,44:17,49:19,54:21,59:23,64:25,65:140,69:27,
    74:29,79:31,84:33,89:35,94:37,96:138,97:124,99:39,104:41,109:43,
    114:45,119:47,124:49,129:51,130:144,134:53,139:55,144:57,149:59,
    154:61,159:63,161:126,164:65,169:67,174:69,179:71,184:73,189:75,
    194:77,199:79,204:81,209:83,214:85,219:87,224:89,229:91,234:93,
    239:95,244:97,249:99,254:101,259:103,260:30,262:52,264:162,268:154,
    269:107,274:109,279:111,284:113,289:115,294:117,299:119,304:121,
    309:123,314:125,319:127,324:129,329:131,334:133,339:135,344:137,
    349:139,354:141,359:143,364:145,369:147,374:149,379:151,384:153,
    386:156,389:155,394:157,399:159,404:161,409:163,516:120,544:152,1023:100
  };
  global.CLUBEF_CATALOG_SOURCE_MAP = Object.freeze({
    DT870_ORIGINAL_CPK_SHA256: 'ae0d8cef26804439e9930ef8959f8d9425754d0e290d056b3e4d1f7b999edd5c',
    BOOSTER_DT870_ORIGINAL_INDEX: Object.freeze(boosterDt870OriginalIndex)
  });
})(globalThis);
