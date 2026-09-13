const vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const common=fs.readFileSync(path.join(__dirname,'../site-common.js'),'utf8');
exports.run=function(source,context,options){
 const env=Object.assign({URL,AbortController,setTimeout,clearTimeout,fetch},context);
 if(env.window&&!env.window.SiteNovoCommon)vm.runInNewContext(common,env);
 return vm.runInNewContext(source,env,options);
};
exports.homeNode=function(){
 let base='',parts={};
 return {set innerHTML(value){base=value;parts={};},get innerHTML(){return base+Object.values(parts).join('');},querySelector(selector){return {set innerHTML(value){parts[selector]=value;}}}};
};
