(function(root){
function evaluate(sheet,address,cache=new Map(),visiting=new Set()){
 if(cache.has(address))return cache.get(address);if(visiting.has(address))throw Error('循環參照');visiting.add(address);
 const raw=sheet.cells[address]?.value;let result;
 if(typeof raw!=='string'||!raw.startsWith('=')){result=typeof raw==='number'?raw:0;}else{
 const source=raw.slice(1).replace(/\$/g,'').toUpperCase(),tokens=source.match(/SUM|[A-Z]+[1-9]\d*|(?:\d+(?:\.\d*)?|\.\d+)|[+\-*/():,]/g)||[];
 if(tokens.join('')!==source.replace(/\s/g,''))throw Error('不支援的公式');let i=0;
 const ref=a=>evaluate(sheet,a,cache,visiting);
 function atom(){const t=tokens[i++];if(t==='-')return -atom();if(t==='+')return atom();if(t==='('){const n=expr();if(tokens[i++]!==')')throw Error('括號錯誤');return n;}if(t==='SUM'){if(tokens[i++]!=='(')throw Error('SUM 格式錯誤');let n=0;do{const a=tokens[i];if(/^[A-Z]+\d+$/.test(a||'')&&tokens[i+1]===':'){i+=2;const b=tokens[i++];const [ac,ar]=decode(a),[bc,br]=decode(b);for(let r=Math.min(ar,br);r<=Math.max(ar,br);r++)for(let c=Math.min(ac,bc);c<=Math.max(ac,bc);c++)n+=ref(encode(c,r));}else n+=expr();if(tokens[i]!==',')break;i++;}while(true);if(tokens[i++]!==')')throw Error('SUM 括號錯誤');return n;}if(/^[A-Z]+\d+$/.test(t||''))return ref(t);if(t!==undefined&&/^\d*\.?\d+$/.test(t))return Number(t);throw Error('公式格式錯誤');}
 function term(){let n=atom();while(['*','/'].includes(tokens[i])){const op=tokens[i++],b=atom();if(op==='/'&&b===0)throw Error('除數為零');n=op==='*'?n*b:n/b;}return n;}
 function expr(){let n=term();while(['+','-'].includes(tokens[i])){const op=tokens[i++],b=term();n=op==='+'?n+b:n-b;}return n;}
 result=expr();if(i!==tokens.length||!Number.isFinite(result))throw Error('公式計算錯誤');
 }visiting.delete(address);cache.set(address,result);return result;
}
function decode(a){const m=/^([A-Z]+)(\d+)$/.exec(a);if(!m)throw Error('儲存格參照錯誤');let c=0;for(const ch of m[1])c=c*26+ch.charCodeAt(0)-64;return [c,Number(m[2])];}
function encode(c,r){let s='';while(c>0){c--;s=String.fromCharCode(65+c%26)+s;c=Math.floor(c/26);}return s+r;}
root.WorkbookMath={evaluate,encode,decode};if(typeof module!=='undefined')module.exports=root.WorkbookMath;
})(globalThis);
