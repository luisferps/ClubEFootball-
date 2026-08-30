'use strict';
(function installMetadataV46(global){
  const base=global.CLUBEF_CORE, reader=global.CLUBEF_CONTRACT_READER;
  if(!base||!reader) throw new Error('metadata-v46-runtime requer core e leitor');
  let plan=null;
  const previousValidate=base.validateSourceByContract;
  const TD=new TextDecoder('utf-8');
  const u32=(b,o)=>(b[o]|(b[o+1]<<8)|(b[o+2]<<16)|(b[o+3]<<24))>>>0;
  const u32be=(b,o)=>((b[o]<<24)|(b[o+1]<<16)|(b[o+2]<<8)|b[o+3])>>>0;
  const u16be=(b,o)=>((b[o]<<8)|b[o+1])>>>0;
  const hex=b=>[...b].map(v=>v.toString(16).padStart(2,'0')).join('');
  function rows(table){const found=(plan?.catalogos||[]).find(x=>x.schema==='clube_novo'&&x.table===table);if(!found?.rows?.length)throw new Error(`catálogo ausente: clube_novo.${table}`);return found.rows;}
  function maybeRows(table){return (plan?.catalogos||[]).find(x=>x.schema==='clube_novo'&&x.table===table)?.rows||[];}
  function field(key){const f=reader.requirePlan(plan).fields.get(key);if(!f)throw new Error(`campo ausente no contrato: ${key}`);return f;}
  function fileForField(key){const f=field(key),file=(plan.arquivos||[]).find(x=>x.arquivo_id===f.arquivo_id);if(!file)throw new Error(`arquivo ausente para ${key}`);return file;}
  function fixed(b,s,w){return reader.readFixedUtf8?reader.readFixedUtf8(b,s,w):(()=>{let e=s;while(e<s+w&&b[e]!==0)e++;return TD.decode(b.subarray(s,e));})();}
  function utfDeobfuscate(data){if(data[0]===0x40&&data[1]===0x55&&data[2]===0x54&&data[3]===0x46)return data;const out=Uint8Array.from(data);let mask=0x655f>>>0;for(let i=0;i<out.length;i++){out[i]^=mask&255;mask=Math.imul(mask,0x4115)>>>0;}return out;}
  function parseUtfTable(data){const d=utfDeobfuscate(data),size=u32be(d,4),block=d.subarray(8,8+size),rowsOffset=u32be(block,0),stringsOffset=u32be(block,4),dataOffset=u32be(block,8),columnCount=u16be(block,16),rowLength=u16be(block,18),rowCount=u32be(block,20),strings=block.subarray(stringsOffset,dataOffset);const readString=o=>{let e=o;while(e<strings.length&&strings[e]!==0)e++;return TD.decode(strings.subarray(o,e));};const readValue=(type,b,o)=>{if(type===0||type===1)return[b[o],1];if(type===2||type===3)return[u16be(b,o),2];if(type===4||type===5)return[u32be(b,o),4];if(type===6||type===7)return[u32be(b,o)*4294967296+u32be(b,o+4),8];if(type===8)return[0,4];if(type===0xA)return[readString(u32be(b,o)),4];if(type===0xB)return[[u32be(b,o),u32be(b,o+4)],8];throw new Error(`tipo @UTF não suportado: ${type}`);};let p=24;const cols=[];for(let i=0;i<columnCount;i++){const flag=block[p++],nameOffset=u32be(block,p);p+=4;const storage=flag&0xf0,type=flag&15;let constant=null;if(storage===0x30){const r=readValue(type,block,p);constant=r[0];p+=r[1];}cols.push({name:readString(nameOffset),storage,type,constant});}const result=[];for(let ri=0;ri<rowCount;ri++){let o=rowsOffset+ri*rowLength;const row={};for(const c of cols){if(c.storage===0x30){row[c.name]=c.constant;continue;}if(c.storage===0x10){row[c.name]=0;continue;}const r=readValue(c.type,block,o);row[c.name]=r[0];o+=r[1];}result.push(row);}return result;}
  function decompressCriLayla(src){if(!(src[0]===0x43&&src[1]===0x52&&src[2]===0x49))return src;const usize=u32(src,8),hoff=u32(src,12),out=new Uint8Array(usize),header=src.subarray(16+hoff,16+hoff+0x100),data=src.subarray(16,16+hoff);let pos=data.length*8-1;const getBits=n=>{let v=0;for(let i=0;i<n;i++){const bi=pos>>3,b=pos&7;v=(v<<1)|((data[bi]>>(7-b))&1);pos--;}return v;};let w=usize-1;while(w>=0){if(getBits(1)){let ref=w+getBits(13)+3,len=3,done=false;for(const width of[2,3,5]){const n=getBits(width);len+=n;if(n!==(1<<width)-1){done=true;break;}}if(!done){let n=getBits(8);len+=n;while(n===255){n=getBits(8);len+=n;}}for(let i=0;i<len;i++){out[w]=out[ref];w--;ref--;}}else{out[w]=getBits(8);w--;}}const result=new Uint8Array(header.length+out.length);result.set(header);result.set(out,header.length);return result;}
  function extractCpk(data){if(!(data[0]===0x43&&data[1]===0x50&&data[2]===0x4b))throw new Error('arquivo não é CPK');const header=parseUtfTable(data.subarray(16))[0],toc=header.TocOffset,content=header.ContentOffset,files={};if(toc)for(const row of parseUtfTable(data.subarray(toc+16))){const base=content&&content<=toc?content:toc,absolute=base+row.FileOffset;let chunk=data.subarray(absolute,absolute+row.FileSize);if(chunk[0]===0x43&&chunk[1]===0x52&&chunk[2]===0x49)chunk=decompressCriLayla(chunk);files[row.FileName]=chunk;}return files;}
  const WESYS_KEYS={1:[378445824,774547186,214490323],2:[0xED5B2960,1246903118,0xF3A31BAD]};
  async function inflate(bytes){const stream=new DecompressionStream('deflate');return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(stream)).arrayBuffer());}
  async function unpackWesys(data){const nibble=data[1]&15,csize=u32(data,8),osize=u32(data,12),buffer=Uint8Array.from(data.subarray(16,16+csize)),initial=WESYS_KEYS[nibble]||[0,0,0];let x=initial[0]>>>0,y=initial[1]>>>0,z=initial[2]>>>0,w=(((osize<<16)>>>0)|csize)>>>0;const aligned=(csize>>2)*4;for(let o=0;o<aligned;o+=4){const t=(x^((x<<11)>>>0))>>>0,prev=w;x=y;y=z;z=w;w=(prev^(((prev>>>11)^t)>>>8)^t)>>>0;const value=(u32(buffer,o)^w)>>>0;buffer[o]=value&255;buffer[o+1]=(value>>>8)&255;buffer[o+2]=(value>>>16)&255;buffer[o+3]=(value>>>24)&255;}return inflate(buffer);}
  async function rawFile(cpks,role,name,recordSize=null,verify=true){const packed=cpks[role]?.[name];if(!packed)throw new Error(`${name} ausente em ${role}`);const raw=await unpackWesys(packed),hash=await reader.sha256(raw);const spec=(plan.arquivos||[]).find(x=>x.arquivo===name&&x.papel_fonte===role);const size=Number(spec?.tamanho_registro??recordSize);const prefix=Number(spec?.prefixo_bytes??(size?raw.length%size:0));if(size&&((raw.length-prefix)%size!==0))throw new Error(`${name} não respeita tamanho de registro em ${role}`);if(verify&&spec&&hash!==String(spec.sha256_arquivo).toLowerCase())throw new Error(`fingerprint divergente: ${role}/${name}`);return{raw,hash,size,prefix};}
  function duplicateIds(records){const seen=new Set(),dup=[];for(const r of records){if(seen.has(String(r.id)))dup.push(String(r.id));seen.add(String(r.id));}return[...new Set(dup)];}
  async function physicalCatalog(cpks,role,key){const f=field(key),spec=(plan.arquivos||[]).find(x=>x.arquivo_id===f.arquivo_id),item=await rawFile(cpks,role,spec.arquivo,spec.tamanho_registro,role==='dt870_updated'),records=[];const prefix=item.prefix;for(let o=prefix;o<item.raw.length;o+=item.size){const rb=item.raw.subarray(o,o+item.size),id=f.tipo_leitura==='byte_le'?reader.readByteLE(item.raw,o+Number(f.byte_offset),Number(f.largura_bytes)):reader.readBitsLE(item.raw,o,Number(f.bit_inicio),Number(f.largura_bits));records.push({id:String(id),raw_hex:hex(rb),record_sha256:await reader.sha256(rb),source_role:role,record_index:(o-prefix)/item.size,source_file_sha256:item.hash});}return{records,duplicate_ids:duplicateIds(records),record_size:item.size,file:spec.arquivo,hash:item.hash};}
  function fingerprint(record){return{...record,fingerprint:base.stableJson(record)};}

  const impetosLayoutAtual=impetos;
  async function impetosFailClosed(cpks){
    // O DT870 Steam observado em 2026-08-30 tem prefixo de 24 bytes e
    // registros cujo restante semântico não obedece ao layout atual. Ele é
    // preservado como evidência histórica por registro, mas nunca participa
    // da união canônica nem recebe efeitos/condições decodificados pelo layout
    // da atualização. Isso impede que um deslocamento aparente de código seja
    // promovido sem prova física completa.
    const decoded=await impetosLayoutAtual(cpks);
    const semanticRoles=['dt200','dt870_updated'];
    const records=[];
    for(const source of decoded.records){
      const sourceDetails=Object.fromEntries(semanticRoles.filter(role=>(source.source_details?.[role]||[]).length).map(role=>[role,source.source_details[role]]));
      const origins=semanticRoles.filter(role=>sourceDetails[role]);
      if(!origins.length)continue;
      const preferred_source=origins.includes('dt870_updated')?'dt870_updated':'dt200';
      const preferred=sourceDetails[preferred_source][0]||{};
      const rawType=preferred.tipo_condicao_raw??null;
      const isVacancy=source.id==='136'&&rawType===4;
      const isRaw4=rawType===4;
      const clean={
        id:source.id,
        origins,
        preferred_source,
        source_fingerprints:Object.fromEntries(origins.map(role=>[role,source.source_fingerprints?.[role]??null])),
        source_details:sourceDetails,
        tipo_condicao_raw:isRaw4?null:rawType,
        tipo_condicao_status:isVacancy?'vaga_de_slot':(isRaw4?'registro_nao_impeto_raw4':(rawType===null?'nao_coletado':'coletado')),
        vaga_de_slot:isVacancy,
        criterio_codigo:preferred.criterio_codigo??null,
        alvo_tipo:preferred.alvo_tipo??null,
        alvo_codigo:preferred.alvo_codigo??null,
        classe_candidato:preferred.classe_candidato??null,
        classe_dono:preferred.classe_dono??null,
        corte_raw:preferred.corte_raw??null,
        corte:preferred.corte??null,
        efeito_maximo:preferred.efeito_maximo??null,
        faixas:preferred.faixas||[],
        efeitos:preferred.efeitos||[],
        tipo_espelho_bit:preferred.tipo_espelho_bit,
        tipo_espelho_largura:preferred.tipo_espelho_largura
      };
      clean.fingerprint=base.stableJson({id:clean.id,origins,source_fingerprints:clean.source_fingerprints,tipo_condicao_raw:clean.tipo_condicao_raw,tipo_condicao_status:clean.tipo_condicao_status});
      records.push(clean);
    }
    const boosterFile=fileForField('impeto.catalogo.codigo');
    const size=Number(decoded.record_size||boosterFile.tamanho_registro);
    const codeField=field('impeto.catalogo.codigo');
    const codeBit=Number(codeField.bit_inicio);
    const codeWidth=Number(codeField.largura_bits);
    const original=await rawFile(cpks,'dt870_original',boosterFile.arquivo,size,true);
    const historicalRecords=[];
    for(let offset=original.prefix,index=0;offset<original.raw.length;offset+=size,index++){
      const bytes=original.raw.subarray(offset,offset+size);
      historicalRecords.push({
        record_index:index,
        record_number:index+1,
        byte_offset:offset,
        raw_code:reader.readBitsLE(original.raw,offset,codeBit,codeWidth),
        code_bit:codeBit,
        code_width:codeWidth,
        record_sha256:await reader.sha256(bytes),
        source_file_sha256:original.hash,
        source_role:'dt870_original',
        semantic_status:'layout_legado_sem_decodificador_comprovado',
        canonical_identity:null,
        comparison_action:'alerta_historico_fail_closed'
      });
    }
    return{
      ...decoded,
      records,
      source_policy:'DT200 e DT870 atualizado formam a união canônica; DT870 Steam é evidência histórica isolada até existir decodificador semântico comprovado',
      historical_source:{
        source_role:'dt870_original',
        file:boosterFile.arquivo,
        record_size:size,
        prefix_bytes:original.prefix,
        source_file_sha256:original.hash,
        semantic_status:'layout_legado_sem_decodificador_comprovado',
        canonical_merge_enabled:false,
        records:historicalRecords
      }
    };
  }
  impetos=impetosFailClosed;

  async function technicians(cpks,texts){const coachFile=fileForField('tecnico.id'),countryFile=fileForField('nacionalidade.codigo'),coachItem=await rawFile(cpks,'dt870_updated',coachFile.arquivo,coachFile.tamanho_registro),countryItem=await rawFile(cpks,'dt870_updated',countryFile.arquivo,countryFile.tamanho_registro);const cf={id:field('tecnico.id'),jp:field('tecnico.nome.jp'),en:field('tecnico.nome.en'),cn:field('tecnico.nome.cn'),age:field('tecnico.idade.raw'),nat:field('tecnico.nacionalidade.codigo'),aff:field('tecnico.afinidade.codigo'),b1:field('tecnico.boost.1'),b2:field('tecnico.boost.2')};const nf={code:field('nacionalidade.codigo'),name:field('nacionalidade.nome_pt_br'),sigla:field('nacionalidade.sigla')};const nats=[],natByCode=new Map();for(let o=0,ri=0;o<countryItem.raw.length;o+=countryItem.size,ri++){const code=reader.readBitsLE(countryItem.raw,o,Number(nf.code.bit_inicio),Number(nf.code.largura_bits)),r=fingerprint({id:String(code),codigo_jogo:code,nome_pt_br:fixed(countryItem.raw,o+Number(nf.name.byte_offset),Number(nf.name.largura_bytes)),sigla:fixed(countryItem.raw,o+Number(nf.sigla.byte_offset),Number(nf.sigla.largura_bytes)),source_role:'dt870_updated',arquivo:countryFile.arquivo,record_index:ri,record_size:countryItem.size,codigo_bit:Number(nf.code.bit_inicio),codigo_largura:Number(nf.code.largura_bits),nome_offset:Number(nf.name.byte_offset),nome_largura:Number(nf.name.largura_bytes),nome_codificacao:'utf-8',sigla_offset:Number(nf.sigla.byte_offset),sigla_largura:Number(nf.sigla.largura_bytes),source_file_sha256:countryItem.hash,presente_dt200:true,presente_dt870_original:true,presente_dt870_atualizacao:true,ativo:true});if(natByCode.has(code))throw new Error(`nacionalidade duplicada ${code}`);nats.push(r);natByCode.set(code,r);}
    const styleRefs=rows('estilo_jogo_tecnico').filter(x=>x.pode_rodar!==false).sort((a,b)=>Number(a.ordem)-Number(b.ordem));const affinityRefs=rows('afinidade_tecnico_jogo'),attrOrder=rows('atributo_ordem_otimizador'),affinityText=(texts.records||[]).find(r=>r.id==='Any1W:495');const affinities=affinityRefs.map(source=>fingerprint({id:String(source.codigo_jogo),codigo_jogo:Number(source.codigo_jogo),nome_pt:source.nome_pt??null,nome_tela:source.nome_tela??null,ausencia_legitima:Boolean(source.ausencia_legitima),rotulo_confirmado:Boolean(source.rotulo_confirmado),source_role:'dt870_updated',arquivo:source.arquivo_fonte||coachFile.arquivo,bit:Number(source.bit),largura:Number(source.largura),source_file_sha256:coachItem.hash,texto_source_role:source.codigo_jogo===5?'dt261_bra':null,texto_arquivo:source.codigo_jogo===5?(source.arquivo_texto||'all.str'):null,texto_secao:source.codigo_jogo===5?(source.secao_texto||affinityText?.secao||null):null,texto_id:source.codigo_jogo===5?(source.id_texto??affinityText?.id_texto??null):null,pode_rodar:Boolean(source.pode_rodar),falta_o_que:source.falta_o_que??null,ativo:true}));
    const tech=[];for(let o=0,ri=0;o<coachItem.raw.length;o+=coachItem.size,ri++){const id=String(reader.readByteLE(coachItem.raw,o+Number(cf.id.byte_offset),Number(cf.id.largura_bytes))),natCode=reader.readBitsLE(coachItem.raw,o,Number(cf.nat.bit_inicio),Number(cf.nat.largura_bits)),nat=natByCode.get(natCode);if(!nat)throw new Error(`técnico ${id} referencia nacionalidade ${natCode} ausente`);const prof={},profPhysical={};for(const s of styleRefs){const value=reader.readBitsLE(coachItem.raw,o,Number(s.bit),Number(s.largura));if(s.codigo!=='overload'||value){prof[s.codigo]=value;profPhysical[s.codigo]={bit:Number(s.bit),largura:Number(s.largura)};}}const boosts=[];for(const [ord,f] of [[1,cf.b1],[2,cf.b2]]){const encoded=reader.readBitsLE(coachItem.raw,o,Number(f.bit_inicio),Number(f.largura_bits));if(encoded){const idx=encoded-1;if(!attrOrder.some(a=>Number(a.indice_otimizador)===idx))throw new Error(`boost de técnico sem atributo canônico ${idx}`);boosts.push({ordem:ord,atributo_idx_canonico:idx,delta:Number(f.transformacao?.delta??1),bit:Number(f.bit_inicio),largura:Number(f.largura_bits)});}}const ageRaw=reader.readBitsLE(coachItem.raw,o,Number(cf.age.bit_inicio),Number(cf.age.largura_bits));const r={id,nome_jp:fixed(coachItem.raw,o+Number(cf.jp.byte_offset),Number(cf.jp.largura_bytes)),nome_en:fixed(coachItem.raw,o+Number(cf.en.byte_offset),Number(cf.en.largura_bytes)),nome_cn:fixed(coachItem.raw,o+Number(cf.cn.byte_offset),Number(cf.cn.largura_bytes)),proficiencias:prof,proficiencias_fisico:profPhysical,boosts,idade:ageRaw+14,idade_valor_fisico:ageRaw,nacionalidade_codigo:natCode,nacionalidade_nome_pt_br:nat.nome_pt_br,nacionalidade_sigla:nat.sigla,afinidade_codigo:reader.readBitsLE(coachItem.raw,o,Number(cf.aff.bit_inicio),Number(cf.aff.largura_bits)),source_role:'dt870_updated',arquivo:coachFile.arquivo,record_index:ri,record_size:coachItem.size,source_file_sha256:coachItem.hash,field_contract:{idade:{bit:Number(cf.age.bit_inicio),largura:Number(cf.age.largura_bits),transformacao:'valor_fisico + 14'},nacionalidade:{bit:Number(cf.nat.bit_inicio),largura:Number(cf.nat.largura_bits),resolve_em:'nacionalidade_jogo'},afinidade:{bit:Number(cf.aff.bit_inicio),largura:Number(cf.aff.largura_bits),zero:'ausencia_legitima'}},ativo:true};tech.push(fingerprint(r));}
    if(duplicateIds(tech).length)throw new Error('Coach.bin contém IDs duplicados');return{technicians:tech,nationalities:nats,affinities,coach_hash:coachItem.hash,country_hash:countryItem.hash};}

  async function impetos(cpks){const impetoCatalog=rows('impeto_jogo'),effectRefs=rows('impeto_atributo_jogo'),conditionRefs=rows('impeto_condicao_jogo'),memberRefs=rows('impeto_condicao_liga_membro_jogo');const boosterFile=fileForField('impeto.catalogo.codigo'),size=Number(impetoCatalog[0]?.tamanho_registro||boosterFile.tamanho_registro),codeBit=Number(impetoCatalog[0]?.bit_codigo??field('impeto.catalogo.codigo').bit_inicio),codeWidth=Number(impetoCatalog[0]?.largura_codigo??field('impeto.catalogo.codigo').largura_bits);const typeField=field('impeto.tipo.condicao'),natField=field('impeto.condicao.nacionalidade'),leagueField=field('impeto.condicao.liga'),clubField=field('impeto.condicao.clube'),candField=field('impeto.condicao.classe_candidato'),ownerField=field('impeto.condicao.classe_dono'),cutField=field('impeto.condicao.faixa.corte'),levelField=field('impeto.condicao.faixa.efeito_maximo');const typeTemplate=maybeRows('tipo_impeto_jogo')[0]||conditionRefs[0]||{},mirrorBit=Number(typeTemplate.bit_tipo_espelho??conditionRefs[0]?.bit_tipo_espelho),mirrorWidth=Number(typeTemplate.largura_tipo_espelho??conditionRefs[0]?.largura_tipo_espelho),effectMap=new Map();for(const r of effectRefs){const k=Number(r.bit_delta);if(!effectMap.has(k))effectMap.set(k,{codigo_atributo:r.codigo_atributo,largura:Number(r.largura_delta),arquivo_origem:r.arquivo_origem,fonte_origem:r.fonte_origem});else if(effectMap.get(k).codigo_atributo!==r.codigo_atributo)throw new Error(`bit de efeito ambíguo ${k}`);}const byId=new Map(),roleNames=['dt200','dt870_original','dt870_updated'];for(const role of roleNames){const item=await rawFile(cpks,role,boosterFile.arquivo,size,role==='dt870_updated'),prefix=item.prefix;if((item.raw.length-prefix)%size!==0)throw new Error(`PlayerBooster inválido em ${role}`);for(let o=prefix,ri=0;o<item.raw.length;o+=size,ri++){const rb=item.raw.subarray(o,o+size),id=String(reader.readBitsLE(item.raw,o,codeBit,codeWidth)),recordSha=await reader.sha256(rb),typeRaw=reader.readBitsLE(item.raw,o,Number(typeField.bit_inicio),Number(typeField.largura_bits)),classOwner=reader.readBitsLE(item.raw,o,Number(ownerField.bit_inicio),Number(ownerField.largura_bits)),nationality=reader.readBitsLE(item.raw,o,Number(natField.bit_inicio),Number(natField.largura_bits)),league=reader.readBitsLE(item.raw,o,Number(leagueField.bit_inicio),Number(leagueField.largura_bits)),team=reader.readBitsLE(item.raw,o,Number(clubField.bit_inicio),Number(clubField.largura_bits)),classCandidate=reader.readBitsLE(item.raw,o,Number(candField.bit_inicio),Number(candField.largura_bits)),cutRaw=reader.readBitsLE(item.raw,o,Number(cutField.bit_inicio),Number(cutField.largura_bits)),level=reader.readBitsLE(item.raw,o,Number(levelField.bit_inicio),Number(levelField.largura_bits));let criterion='sempre_ativo',targetKind=null,targetCode=null;if(typeRaw===1)criterion='avaliacao_ao_vivo';if(typeRaw===2){if(classOwner>0){criterion='quantidade_jogadores_classe_impeto';targetKind='classe_impeto';targetCode=classOwner;}else if(nationality>0){criterion='quantidade_jogadores_nacionalidade_regiao';targetKind='nacionalidade_regiao';targetCode=nationality;}else if(league!==0&&league!==0xffff){criterion='quantidade_jogadores_liga_categoria';targetKind='liga_categoria';targetCode=league;}else{criterion='quantidade_jogadores_clube_equipe';targetKind='clube_equipe';targetCode=team||null;}}const cutoff=cutRaw+2,ranges=[];if(typeRaw===2&&level>0){let start=1,previous=null;for(let q=1;q<=23;q++){const delta=Math.min(level,Math.max(1,Math.floor(level*q/cutoff)));if(previous!==null&&delta!==previous){ranges.push({quantidade_minima:start,quantidade_maxima:q-1,delta:previous});start=q;}previous=delta;}ranges.push({quantidade_minima:start,quantidade_maxima:23,delta:previous});}const effects=[];for(const [bit,info] of effectMap){const delta=reader.readBitsLE(item.raw,o,bit,info.largura);if(delta>0)effects.push({codigo_atributo:info.codigo_atributo,bit_delta:bit,largura_delta:info.largura,delta,arquivo_origem:info.arquivo_origem||boosterFile.arquivo,fonte_origem:info.fonte_origem||'dt870_atualizacao:PlayerBooster.bin'});}const detail={raw_hex:hex(rb),record_sha256:recordSha,source_role:role,record_index:ri,source_file_sha256:item.hash,tipo_condicao_raw:typeRaw,tipo_condicao_espelho_u32:Number.isInteger(mirrorBit)&&Number.isInteger(mirrorWidth)?reader.readBitsLE(item.raw,o,mirrorBit,mirrorWidth):null,tipo_bit:Number(typeField.bit_inicio),tipo_largura:Number(typeField.largura_bits),tipo_espelho_bit:mirrorBit,tipo_espelho_largura:mirrorWidth,criterio_codigo:criterion,alvo_tipo:targetKind,alvo_codigo:targetCode,alvo_nacionalidade_raw:nationality,alvo_liga_raw:league,alvo_clube_raw:team,classe_candidato:classCandidate,classe_dono:classOwner,corte_raw:cutRaw,corte:cutoff,efeito_maximo:level,faixas:ranges,efeitos:effects};let union=byId.get(id);if(!union){union={id,source_records:{},source_details:{}};byId.set(id,union);}union.source_records[role]=item.hash;if(!union.source_details[role])union.source_details[role]=[];union.source_details[role].push(detail);}}
    const priority=['dt870_updated','dt870_original','dt200'],records=[...byId.values()].map(u=>{const origins=roleNames.filter(r=>u.source_records[r]),preferred_source=priority.find(r=>u.source_records[r]),preferred=(u.source_details[preferred_source]||[])[0]||{},rawType=preferred.tipo_condicao_raw??null,isVacancy=u.id==='136'&&rawType===4,isRaw4=rawType===4,r={id:u.id,origins,preferred_source,source_fingerprints:u.source_records,source_details:u.source_details,tipo_condicao_raw:isRaw4?null:rawType,tipo_condicao_status:isVacancy?'vaga_de_slot':(isRaw4?'registro_nao_impeto_raw4':(rawType===null?'nao_coletado':'coletado')),vaga_de_slot:isVacancy,criterio_codigo:preferred.criterio_codigo??null,alvo_tipo:preferred.alvo_tipo??null,alvo_codigo:preferred.alvo_codigo??null,classe_candidato:preferred.classe_candidato??null,classe_dono:preferred.classe_dono??null,corte_raw:preferred.corte_raw??null,corte:preferred.corte??null,efeito_maximo:preferred.efeito_maximo??null,faixas:preferred.faixas||[],efeitos:preferred.efeitos||[],tipo_espelho_bit:preferred.tipo_espelho_bit,tipo_espelho_largura:preferred.tipo_espelho_largura};r.fingerprint=base.stableJson({id:r.id,origins,source_fingerprints:r.source_fingerprints,tipo_condicao_raw:r.tipo_condicao_raw,tipo_condicao_status:r.tipo_condicao_status});return r;});
    const unitFile=fileForField('impeto.liga_membro.base'),unit=await rawFile(cpks,'dt870_updated',unitFile.arquivo,unitFile.tamanho_registro),layout={};for(const role of['vinculo_anterior','alvo_base','vinculo_posterior']){const ref=memberRefs.find(r=>r.papel_fisico===role);if(ref)layout[role]={bit:Number(ref.bit_inicial),largura:Number(ref.largura)};}const targets=new Set(records.filter(r=>r.preferred_source==='dt870_updated'&&r.alvo_tipo==='liga_categoria').map(r=>Number(r.alvo_codigo))),members=[];for(let o=0,ri=0;o<unit.raw.length;o+=unit.size,ri++){const baseLayout=layout.alvo_base;if(!baseLayout)break;const code=reader.readBitsLE(unit.raw,o,baseLayout.bit,baseLayout.largura);if(!targets.has(code))continue;const rb=unit.raw.subarray(o,o+unit.size),recordSha=await reader.sha256(rb),prev=layout.vinculo_anterior?reader.readBitsLE(unit.raw,o,layout.vinculo_anterior.bit,layout.vinculo_anterior.largura):0,next=layout.vinculo_posterior?reader.readBitsLE(unit.raw,o,layout.vinculo_posterior.bit,layout.vinculo_posterior.largura):0;let order=1;if(prev&&prev!==0xffff){members.push({codigo_liga_alvo_base:code,codigo_liga_membro:prev,ordem_fisica:order++,papel_fisico:'vinculo_anterior',record_index:ri,bit_inicial:layout.vinculo_anterior.bit,largura:layout.vinculo_anterior.largura,source_file_sha256:unit.hash,record_sha256:recordSha});}members.push({codigo_liga_alvo_base:code,codigo_liga_membro:code,ordem_fisica:order++,papel_fisico:'alvo_base',record_index:ri,bit_inicial:baseLayout.bit,largura:baseLayout.largura,source_file_sha256:unit.hash,record_sha256:recordSha});if(next&&next!==0xffff)members.push({codigo_liga_alvo_base:code,codigo_liga_membro:next,ordem_fisica:order,papel_fisico:'vinculo_posterior',record_index:ri,bit_inicial:layout.vinculo_posterior.bit,largura:layout.vinculo_posterior.largura,source_file_sha256:unit.hash,record_sha256:recordSha});}
    return{supported:true,file:boosterFile.arquivo,source_policy:'união por ID com procedência preservada; referências físicas de clube_novo',record_size:size,id_contract:`bit ${codeBit}, largura ${codeWidth}`,records,duplicate_ids:[],liga_membros:members,contract:'clubef-impetos-physical-v1',field_contract:{codigo:{bit:codeBit,largura:codeWidth},tipo:{bit:Number(typeField.bit_inicio),largura:Number(typeField.largura_bits)},tipo_espelho:{bit:mirrorBit,largura:mirrorWidth},nacionalidade:{bit:Number(natField.bit_inicio),largura:Number(natField.largura_bits)},liga:{bit:Number(leagueField.bit_inicio),largura:Number(leagueField.largura_bits)},clube:{bit:Number(clubField.bit_inicio),largura:Number(clubField.largura_bits)},classe_candidato:{bit:Number(candField.bit_inicio),largura:Number(candField.largura_bits)},classe_dono:{bit:Number(ownerField.bit_inicio),largura:Number(ownerField.largura_bits)},corte:{bit:Number(cutField.bit_inicio),largura:Number(cutField.largura_bits),transformacao:'raw + 2'},efeito_maximo:{bit:Number(levelField.bit_inicio),largura:Number(levelField.largura_bits)},liga_membros:{arquivo:unitFile.arquivo,tamanho_registro:unit.size,arquivo_sha256:unit.hash}}};}

  async function extractMetadataByFamilyV46(sourceBytes,sourceDescriptors,log=()=>{}){if(!plan)throw new Error('contrato ativo ainda não foi recebido');const required=['dt870_updated','dt200','dt870_original','dt261_bra'];for(const role of required)if(!sourceBytes[role])throw new Error(`fonte obrigatória ausente: ${role}`);const cpks=Object.fromEntries(required.map(r=>[r,extractCpk(sourceBytes[r])]));const skill=await physicalCatalog(cpks,'dt870_updated','catalogo.habilidade.id'),habilidades={supported:true,file:skill.file,source_policy:'DT870 da atualização',record_size:skill.record_size,id_contract:'id físico fornecido pelo contrato',records:skill.records.map(r=>fingerprint(r)),duplicate_ids:skill.duplicate_ids};log(`habilidades · ${habilidades.records.length}`);const booster=await impetos(cpks);log(`ímpetos · união com procedência: ${booster.records.length}`);const playKey='catalogo.playstyle.id',baseStyle=await physicalCatalog(cpks,'dt200',playKey),overlayStyle=await physicalCatalog(cpks,'dt870_updated',playKey),overlayById=new Map(overlayStyle.records.map(r=>[r.id,r])),baseIds=new Set(baseStyle.records.map(r=>r.id)),unsupportedEntries=overlayStyle.records.filter(r=>!baseIds.has(r.id)).map(r=>({id:r.id,source_role:'dt870_updated',reason:'overlay sem registro semântico correspondente no DT200'})),playstyles={supported:true,file:baseStyle.file,source_policy:'DT200 é a base semântica; DT870 atualizado é somente overlay',record_size:baseStyle.record_size,id_contract:'id físico fornecido pelo contrato',records:baseStyle.records.map(b=>fingerprint({id:b.id,semantic_source:'dt200',base_raw_hex:b.raw_hex,overlay_present:overlayById.has(b.id),overlay_raw_hex:overlayById.get(b.id)?.raw_hex||null})),unsupported_entries:unsupportedEntries,duplicate_ids:[]};log(`playstyles · base DT200: ${playstyles.records.length}`);const textos=await base.extractTextCatalogFromCpk(sourceBytes.dt261_bra);log(`textos · ${textos.records.length}`);const coach=await technicians(cpks,textos),tecnicos={supported:true,file:'Coach.bin + Country.bin',source_policy:'DT870 da atualização; referências físicas canônicas',record_size:fileForField('tecnico.id').tamanho_registro,id_contract:'u64 do contrato',contract:'clubef-tecnicos-carga-v4-sobreposicao',records:coach.technicians,duplicate_ids:[]},nacionalidades={supported:true,file:'Country.bin',source_policy:'DT870 atualizado; referência canônica',record_size:fileForField('nacionalidade.codigo').tamanho_registro,id_contract:'código físico do contrato',contract:'clubef-nacionalidades-v1',records:coach.nationalities,duplicate_ids:[]},afinidades={supported:true,file:'Coach.bin + all.str',source_policy:'código físico + rótulo oficial',id_contract:'afinidade_tecnico_jogo',contract:'clubef-afinidades-tecnico-v1',records:coach.affinities,duplicate_ids:[]};log(`técnicos · ${tecnicos.records.length}; nacionalidades: ${nacionalidades.records.length}; afinidades: ${afinidades.records.length}`);const unsupported=(file,reason,source_policy=null)=>({supported:false,status:'nao_suportado_nesta_atualizacao',file,reason,source_policy,records:[],duplicate_ids:[]}),posicoes={supported:true,file:'Player.bin + catálogo',source_policy:'clube_novo.posicao_jogo',records:rows('posicao_jogo').map(r=>fingerprint({id:String(r.id),codigo_en:r.codigo_en})),duplicate_ids:[]};const catalogs={habilidades,impetos:booster,playstyles,posicoes,textos,tecnicos,nacionalidades,afinidades_tecnico:afinidades,estilos_ia:unsupported('Player.bin','catálogo nominal integral ainda não suportado'),efeitos_de_impeto:{supported:true,file:booster.file,contract:booster.contract,records:booster.records.flatMap(r=>(r.efeitos||[]).map(e=>({codigo_impeto:r.id,...e}))),duplicate_ids:[]},times_e_vinculos:unsupported('Team.bin + PlayerAssignment.bin','layout integral não suportado'),potw:unsupported('PlayerWeekly.bin','layout integral não suportado'),habilidade_extra_de_variacao:unsupported('PlayerVariationPrSkill.bin','layout integral não suportado')};return{contract:'clubef-physical-metadata-v4',source_policy:'por família; endereços de clube_novo',sources:sourceDescriptors,catalogs};}

  function familyRoles(key){const item=(plan?.familias||[]).find(x=>x.chave_familia===key);if(!item)throw new Error(`família ausente do pedido: ${key}`);return[...new Set((item.papeis_fonte||[]).filter(Boolean))];}
  function roleForField(key){const file=fileForField(key);if(!file.papel_fonte)throw new Error(`arquivo sem papel de fonte no contrato: ${key}`);return file.papel_fonte;}
  function notRequested(file,reason){return{supported:false,status:'nao_solicitado_pelo_contrato',file,reason,records:[],duplicate_ids:[]};}
  function coverageBlockedCatalogsFromContract(){
    const output={},seen=new Set();
    for(const mapping of plan?.catalogos_fisicos||[]){
      if(!mapping||mapping.aprovacao_aplicacao_habilitada!==false)continue;
      const key=mapping.chave_resultado_leitura,impacted=mapping.familias_impactadas;
      if(typeof key!=='string'||!key||seen.has(key))throw new Error('contrato de cobertura sem chave de resultado única');
      if(!Array.isArray(impacted)||!impacted.every(item=>typeof item==='string'&&item))throw new Error(`contrato de cobertura sem famílias impactadas: ${key}`);
      if(typeof mapping.estado_cobertura!=='string'||!mapping.estado_cobertura)throw new Error(`contrato de cobertura sem estado: ${key}`);
      seen.add(key);
      // O contrato ainda não prova uma enumeração total de estilo IA. A V5
      // deve explicitar que os bits retornados pelas cartas são monitorados,
      // sem publicar a lista observada como catálogo completo.
      const observedStyleMonitor=mapping.schema==='clube_novo'&&mapping.table==='estilo_ia';
      const coverageState=observedStyleMonitor?'observado_nas_cartas_monitorado':mapping.estado_cobertura;
      output[key]={
        supported:false,
        status:coverageState,
        coverage_complete:false,
        application_eligible:false,
        catalogo:{schema:mapping.schema,table:mapping.table,colunas_chave_canonica:mapping.colunas_chave_canonica||[]},
        origem_fisica_comprovada:Boolean(mapping.evidencia_enumeracao?.fonte_enumeravel_comprovada),
        artefato_fisico_declarado:mapping.artefato_fisico??null,
        papel_fonte_declarado:mapping.papel_fonte??null,
        familias_impactadas:impacted,
        reason:observedStyleMonitor?'os bits observados nas cartas são monitorados; não existe enumeração física integral comprovada':(mapping.motivo_cobertura||'cobertura física não verificável pelo contrato'),
        monitoring:observedStyleMonitor?{
          identity:'bit físico + procedência por carta',
          unknown_member_action:'alertar para revisão e bloquear somente a relação afetada',
          catalog_auto_creation:false,
          label_inference:false
        }:null,
        evidencia:mapping.evidencia_enumeracao||{},
        records:[],duplicate_ids:[]
      };
    }
    return output;
  }
  async function extractMetadataByFamilyTyped(sourceBytes,sourceDescriptors,log=()=>{}){
    if(!plan)throw new Error('contrato ativo ainda não foi recebido');
    const allowed=new Set([...(plan.arquivos||[]).map(x=>x.papel_fonte),...(plan.familias||[]).flatMap(f=>f.papeis_fonte||[])].filter(Boolean));
    for(const role of Object.keys(sourceBytes))if(!allowed.has(role))throw new Error(`fonte fora do pedido tipado: ${role}`);
    const required=[...new Set(['catalogos','tecnicos','impetos','textos'].flatMap(familyRoles))];
    for(const role of required)if(!sourceBytes[role])throw new Error(`fonte contratada ausente para Metadados: ${role}`);
    const cpks=Object.fromEntries(required.map(role=>[role,extractCpk(sourceBytes[role])]));
    const skillRole=roleForField('catalogo.habilidade.id');
    const skill=await physicalCatalog(cpks,skillRole,'catalogo.habilidade.id');
    const habilidades={supported:true,file:skill.file,source_policy:'papel declarado pelo contrato',record_size:skill.record_size,id_contract:'id físico do contrato',records:skill.records.map(fingerprint),duplicate_ids:skill.duplicate_ids};
    log(`habilidades · ${habilidades.records.length}`);
    const textRoles=familyRoles('textos');
    const textRole=textRoles.length===1?textRoles[0]:null;
    const textos=textRole?await base.extractTextCatalogFromCpk(sourceBytes[textRole]):null;
    if(textos)log(`textos · ${textos.records.length}`);
    const technicianRole=roleForField('tecnico.id');
    let tecnicos=notRequested('Coach.bin','o leitor tipado de técnicos requer que Coach.bin seja atendido pelo papel declarado');
    let nacionalidades=notRequested('Country.bin','o leitor tipado de nacionalidades requer que Country.bin seja atendido pelo papel declarado');
    let afinidades=notRequested('Coach.bin + all.str','leitura depende das fontes declaradas de Técnicos e Textos');
    if(technicianRole==='dt870_updated'&&cpks[technicianRole]){
      const coach=await technicians(cpks,textos||{records:[]});
      tecnicos={supported:true,file:'Coach.bin + Country.bin',source_policy:'papel declarado pelo contrato',record_size:fileForField('tecnico.id').tamanho_registro,id_contract:'u64 físico do contrato',records:coach.technicians,duplicate_ids:[]};
      nacionalidades={supported:true,file:'Country.bin',source_policy:'papel declarado pelo contrato',record_size:fileForField('nacionalidade.codigo').tamanho_registro,id_contract:'código físico do contrato',records:coach.nationalities,duplicate_ids:[]};
      afinidades={supported:true,file:'Coach.bin + all.str',source_policy:'FK física e rótulo oficial separado',records:coach.affinities,duplicate_ids:[]};
      log(`técnicos · ${tecnicos.records.length}; nacionalidades: ${nacionalidades.records.length}`);
    }
    const playRole=roleForField('catalogo.playstyle.id');
    const playstyles=cpks[playRole]?(()=>physicalCatalog(cpks,playRole,'catalogo.playstyle.id'))():null;
    const resolvedPlaystyles=playstyles?await playstyles:notRequested('Player.bin','a fonte de playstyles não foi solicitada pelo contrato');
    const impetoRoles=familyRoles('impetos');
    const impetoSupported=impetoRoles.length===3&&['dt200','dt870_original','dt870_updated'].every(role=>impetoRoles.includes(role));
    const impetosCatalog=impetoSupported?await impetos(cpks):notRequested('PlayerBooster.bin','o plano atual não declara todas as fontes históricas exigidas pelo leitor de união; nenhuma fonte foi inferida');
    const posicoes={supported:true,file:'Player.bin + catálogo',source_policy:'FK estável clube_novo.posicao_jogo',records:rows('posicao_jogo').map(r=>fingerprint({id:String(r.id),codigo_en:r.codigo_en})),duplicate_ids:[]};
    const catalogs={habilidades,impetos:impetosCatalog,playstyles:resolvedPlaystyles&&resolvedPlaystyles.records?{supported:true,file:resolvedPlaystyles.file,source_policy:'papel declarado pelo contrato',record_size:resolvedPlaystyles.record_size,id_contract:'id físico do contrato',records:resolvedPlaystyles.records.map(fingerprint),duplicate_ids:resolvedPlaystyles.duplicate_ids}:resolvedPlaystyles,posicoes,textos:textos||notRequested('all.str','a família Textos não declarou fonte única'),tecnicos,nacionalidades,afinidades_tecnico:afinidades,efeitos_de_impeto:impetosCatalog.supported?{supported:true,file:impetosCatalog.file,records:impetosCatalog.records.flatMap(r=>(r.efeitos||[]).map(e=>({codigo_impeto:r.id,...e}))),duplicate_ids:[]}:notRequested('PlayerBooster.bin',impetosCatalog.reason),...coverageBlockedCatalogsFromContract()};
    return{contract:'pedido_leitura_tipado_v1',source_policy:'somente papéis declarados pelo contrato',sources:sourceDescriptors,catalogs};
  }
  async function captureValidate(bytes,p,role){reader.requirePlan(p);plan=p;return previousValidate(bytes,p,role);}
  global.CLUBEF_CORE=Object.freeze({...base,validateSourceByContract:captureValidate,extractMetadataByFamily:extractMetadataByFamilyTyped});
})(globalThis);
