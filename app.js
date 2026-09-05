const baseVehicles={
 'ABC-123':{owner:'Residente Demo',dept:'101',spaces:['1'],type:'auto',relation:'residente'},
 'VER-001':{owner:'Residente Verdi',dept:'205',spaces:['45','46'],type:'auto',relation:'residente'},
 'XYZ-789':{owner:'Visitante autorizado',dept:'1204',spaces:[],type:'auto',relation:'residente'},
 'BIC-001':{owner:'Residente Demo',dept:'101',spaces:['2'],type:'bicicleta',relation:'residente'}
};
function formatPlate(value){const raw=String(value||'').toUpperCase().replace(/[^A-Z0-9]/g,'').slice(0,6);return raw.length>3?raw.slice(0,3)+'-'+raw.slice(3):raw}
function canonicalPlate(value){return formatPlate(value)}
function canonicalizeVehicles(data){const out={};Object.entries(data||{}).forEach(([plate,v])=>{out[canonicalPlate(plate)]={...v}});return out}
let vehicles=canonicalizeVehicles(JSON.parse(localStorage.getItem('verdi_vehicles')||'null')||baseVehicles);
let logs=JSON.parse(localStorage.getItem('verdi_logs')||'[]');
let insideState=JSON.parse(localStorage.getItem('verdi_inside')||'{}');
let selectedPlate='';
const $=id=>document.getElementById(id);
function now(){return new Date().toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
function today(){return new Date().toLocaleDateString('es-PE')}
function basement(n){n=Number(n);return n>=1&&n<=43?'S1':n<=89?'S2':n<=136?'S3':n<=147?'S4':'—'}
function spaceText(v){return v.spaces&&v.spaces.length?v.spaces.map(n=>`${n} (${basement(n)})`).join(', '):'Sin cochera'}
function relationText(v){return v.relation==='inquilino_cochera'?'Inquilino externo · sin Dpto.':'Dpto. '+(v.dept||'—')}
function typeText(v){return v.type==='bicicleta'?'🚲 Bicicleta':v.type==='moto'?'🏍️ Moto':v.type==='auto'?'🚗 Auto':'🚙 Otro'}
function departments(){const a=[];a.push('101','102','103');for(let floor=2;floor<=15;floor++)for(let n=1;n<=9;n++)a.push(`${floor}${String(n).padStart(2,'0')}`);return a}
function renderDepartments(){$('department').innerHTML='<option value="">Seleccione Dpto.</option>'+departments().map(d=>`<option value="${d}">${d}</option>`).join('')}
function save(){localStorage.setItem('verdi_vehicles',JSON.stringify(vehicles));localStorage.setItem('verdi_logs',JSON.stringify(logs));localStorage.setItem('verdi_inside',JSON.stringify(insideState))}
function getVehicle(plate){return vehicles[canonicalPlate(plate)]||null}
function getInside(){return Object.entries(insideState).filter(([,v])=>v).map(([plate])=>canonicalPlate(plate)).filter(p=>vehicles[p]).sort((a,b)=>(vehicles[a].lastEntryAt||'').localeCompare(vehicles[b].lastEntryAt||''))}
function getRecentReturns(){
 const latest={};
 logs.filter(x=>x&&x.plate).forEach(x=>{const p=canonicalPlate(x.plate);if(!latest[p]||(x.ts||0)>(latest[p].ts||0))latest[p]={...x,plate:p}});
 return Object.values(latest).filter(x=>x.type==='exit'&&!insideState[x.plate]&&vehicles[x.plate]).sort((a,b)=>(b.ts||0)-(a.ts||0)).slice(0,20);
}
function seedDemoExits(){
 if(localStorage.getItem('verdi_demo_seed_v2')==='1')return;
 vehicles=canonicalizeVehicles(baseVehicles);insideState={};
 const base=Date.now()-600000;
 logs=Object.keys(vehicles).map((plate,i)=>{const v=vehicles[plate];return {plate,owner:v.owner,dept:v.dept||'—',spaces:spaceText(v),type:'exit',authorized:true,time:new Date(base+i*60000).toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit',second:'2-digit'}),date:new Date(base+i*60000).toLocaleDateString('es-PE'),ts:base+i*60000}}).reverse();
 localStorage.setItem('verdi_demo_seed_v2','1');save();
}
function buildHistory(){
 const rows=[];const open={};
 [...logs].sort((a,b)=>(a.ts||0)-(b.ts||0)).forEach(x=>{
  const plate=canonicalPlate(x.plate);
  if(x.type==='entry'){const row={plate,dept:x.dept||'—',owner:x.owner||'—',spaces:x.spaces||'—',entryDate:x.date||'—',entryTime:x.time||'—',exitDate:'—',exitTime:'—',status:'DENTRO',ts:x.ts||0};rows.push(row);open[plate]=row}
  else if(x.type==='exit'){const row=open[plate];if(row){row.exitDate=x.date||'—';row.exitTime=x.time||'—';row.status='FUERA';delete open[plate]}else rows.push({plate,dept:x.dept||'—',owner:x.owner||'—',spaces:x.spaces||'—',entryDate:'—',entryTime:'—',exitDate:x.date||'—',exitTime:x.time||'—',status:'FUERA',ts:x.ts||0})}
 });return rows.reverse();
}
function renderFastLists(){
 const inside=$('insideList'),returns=$('returnList');
 const inPlates=getInside().reverse();
 inside.innerHTML=inPlates.length?inPlates.map(plate=>{const v=vehicles[plate];return `<div class="fast-row"><div class="fast-main"><b>${plate}</b><small>${relationText(v)} · ${v.owner} · ${spaceText(v)}</small></div><button class="fast-btn fast-out" data-fast="${plate}" data-action="exit">SALIÓ</button></div>`}).join(''):'<div class="fast-empty">No hay vehículos dentro en este momento.</div>';
 const recent=getRecentReturns();
 returns.innerHTML=recent.length?recent.map(x=>{const v=vehicles[x.plate];return `<div class="fast-row"><div class="fast-main"><b>${x.plate}</b><small>${relationText(v)} · salió ${x.time} · ${v.owner}</small></div><button class="fast-btn fast-in" data-fast="${x.plate}" data-action="entry">ENTRÓ</button></div>`}).join(''):'<div class="fast-empty">Aquí aparecerán los vehículos que salgan y quedarán listos para registrar su retorno.</div>';
 document.querySelectorAll('[data-fast]').forEach(b=>b.onclick=()=>{selectedPlate=canonicalPlate(b.dataset.fast);$('plate').value=selectedPlate;showVehicle(selectedPlate);movement(b.dataset.action)});
}
function render(){
 $('inside').textContent=getInside().length;$('events').textContent=logs.filter(x=>x.date===today()).length;$('authorized').textContent=Object.keys(vehicles).length;
 const rows=buildHistory();$('history').innerHTML=rows.slice(0,50).map(x=>`<tr><td><b>${x.dept}</b></td><td><b>${x.plate}</b><br><small>${x.owner}</small></td><td>${x.exitDate}<br><b>${x.exitTime}</b></td><td>${x.entryDate}<br><b>${x.entryTime}</b></td><td>${x.spaces}</td><td><span class="badge ${x.status==='DENTRO'?'in':'out'}">${x.status}</span></td></tr>`).join('')||'<tr><td colspan="6">Sin movimientos registrados.</td></tr>';
 renderFastLists();save();
}
function updateNewEntryState(){
 const plate=canonicalPlate($('plate').value);const owner=$('newOwner').value.trim();const relation=$('newRelation').value;const dept=$('newDept').value.trim();const spaces=$('newSpaces').value.split(',').map(x=>x.trim()).filter(Boolean);const type=$('newType').value;
 const ok=plate.replace('-','').length===6&&!!owner&&(relation==='inquilino_cochera'?spaces.length>0:!!dept)&&(type!=='bicicleta'||!!dept);
 $('entryBtn').disabled=!ok;$('exitBtn').disabled=true;
}
function showVehicle(plate){
 selectedPlate=canonicalPlate(plate);$('plate').value=selectedPlate;const v=getVehicle(selectedPlate);const info=$('vehicleInfo');$('newVehicle').classList.add('hidden');
 if(!v){info.classList.remove('hidden');info.innerHTML='<b>⚠ Placa no registrada</b><br>Complete los datos del responsable para registrarla y realizar la ENTRADA en el mismo paso.';$('exitBtn').disabled=true;prepareNew();return null}
 info.classList.remove('hidden');info.innerHTML=`<div class="vehicle-main"><b>${v.owner}</b><strong>${relationText(v)}</strong></div><div>${typeText(v)} &nbsp; · &nbsp; 🅿️ <b>${spaceText(v)}</b></div><div>Estado: <b>${insideState[selectedPlate]?'🟢 DENTRO':'⚪ FUERA'}</b></div>`;
 $('entryBtn').disabled=!!insideState[selectedPlate];$('exitBtn').disabled=!insideState[selectedPlate];return v;
}
function prepareNew(){$('newVehicle').classList.remove('hidden');$('newDept').value=$('department').value||'';updateNewEntryState()}
function searchPlate(){const p=canonicalPlate($('plate').value);$('plate').value=p;if(!p){$('message').textContent='⚠ Escriba una placa.';return}showVehicle(p)}
function searchDept(){
 const dept=$('department').value,box=$('deptCars');if(!dept){box.innerHTML='';return}
 const list=Object.entries(vehicles).filter(([,v])=>v.dept===dept);box.innerHTML=list.length?`<div class="dept-title">Vehículos de Dpto. ${dept}</div>`+list.map(([plate,v])=>`<div class="car-row"><div><b>${plate}</b><br><span>${v.owner} · ${typeText(v)} · 🅿️ ${spaceText(v)} · ${insideState[plate]?'🟢 DENTRO':'⚪ FUERA'}</span></div><button class="quick ${insideState[plate]?'quick-out':'quick-in'}" data-quick="${plate}" data-action="${insideState[plate]?'exit':'entry'}">${insideState[plate]?'SALIÓ':'ENTRÓ'}</button></div>`).join(''):'<div class="empty">No hay vehículos registrados para este Dpto. Puede registrar una nueva placa al ingresar.</div>';
 box.querySelectorAll('[data-quick]').forEach(b=>b.onclick=()=>{selectedPlate=canonicalPlate(b.dataset.quick);$('plate').value=selectedPlate;showVehicle(selectedPlate);movement(b.dataset.action)});
}
function movement(type){
 let plate=canonicalPlate(selectedPlate||$('plate').value);$('plate').value=plate;let v=getVehicle(plate);
 if(!v){
  if(type!=='entry'){$('message').textContent='⚠ Una placa nueva solo puede registrarse como ENTRADA.';return}
  if(!$('registerVehicle').checked){$('message').textContent='⚠ Marque Registrar esta placa para continuar.';return}
  const owner=$('newOwner').value.trim(),relation=$('newRelation').value,dept=$('newDept').value.trim(),spaces=$('newSpaces').value.split(',').map(x=>x.trim()).filter(Boolean),vehicleType=$('newType').value;
  if(!owner){$('message').textContent='⚠ Complete el responsable.';return}
  if(!/^[A-Z0-9]{3}-[A-Z0-9]{3}$/.test(plate)){$('message').textContent='⚠ La placa debe tener 6 caracteres alfanuméricos.';return}
  if(vehicleType==='bicicleta'&&!dept){$('message').textContent='⚠ La bicicleta debe estar asociada a un Dpto.';return}
  if(relation==='residente'&&!dept){$('message').textContent='⚠ Complete el Dpto. del residente.';return}
  if(relation==='inquilino_cochera'&&spaces.length===0){$('message').textContent='⚠ Para un inquilino externo indique al menos una cochera.';return}
  v=vehicles[plate]={owner,dept:relation==='inquilino_cochera'?'':dept,spaces,type:vehicleType,relation,notes:$('newNotes').value.trim()};
 }
 if(type==='entry'&&insideState[plate]){$('message').textContent='⚠ El vehículo ya figura DENTRO.';return}
 if(type==='exit'&&!insideState[plate]){$('message').textContent='⚠ El vehículo ya figura FUERA.';return}
 const ts=Date.now();if(type==='entry')v.lastEntryAt=new Date(ts).toISOString();insideState[plate]=type==='entry';logs.unshift({plate,owner:v.owner,dept:v.dept||'—',spaces:spaceText(v),type,authorized:true,time:now(),date:today(),ts});
 $('message').textContent=type==='entry'?'✅ ENTRADA REGISTRADA':'✅ SALIDA REGISTRADA';selectedPlate=plate;showVehicle(plate);render();if($('department').value)searchDept();
}
$('searchBtn').onclick=searchPlate;$('entryBtn').onclick=()=>movement('entry');$('exitBtn').onclick=()=>movement('exit');$('deptBtn').onclick=searchDept;$('department').onchange=searchDept;
$('plate').addEventListener('input',e=>{
 e.target.value=canonicalPlate(e.target.value);selectedPlate=e.target.value;
 $('message').textContent='';
 if(!e.target.value){$('vehicleInfo').classList.add('hidden');$('newVehicle').classList.add('hidden');$('entryBtn').disabled=true;$('exitBtn').disabled=true;return}
 if(getVehicle(e.target.value)){showVehicle(e.target.value)}else if(e.target.value.replace('-','').length===6){prepareNew()}else{$('vehicleInfo').classList.add('hidden');$('newVehicle').classList.add('hidden');$('entryBtn').disabled=true;$('exitBtn').disabled=true}
});
$('plate').addEventListener('keydown',e=>{if(e.key==='Enter')searchPlate()});
['newOwner','newRelation','newDept','newType','newSpaces','newNotes'].forEach(id=>$(id).addEventListener('input',updateNewEntryState));
$('newRelation').addEventListener('change',updateNewEntryState);$('newType').addEventListener('change',updateNewEntryState);
$('registerVehicle').onchange=updateNewEntryState;
$('clearBtn').onclick=()=>{if(confirm('¿Borrar movimientos y restaurar vehículos de demo?')){localStorage.removeItem('verdi_demo_seed_v2');vehicles=canonicalizeVehicles(baseVehicles);logs=[];insideState={};seedDemoExits();render();showVehicle('')}};
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{$('plate').value=canonicalPlate(b.dataset.plate);searchPlate()});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');const mode=t.dataset.mode;$('plateSearch').classList.toggle('hidden',mode!=='plate');$('deptSearch').classList.toggle('hidden',mode!=='dept');$('vehicleInfo').classList.add('hidden');$('newVehicle').classList.add('hidden');$('message').textContent=''});
$('returnToggle').onclick=()=>{$('returnList').classList.toggle('collapsed');$('returnToggle').classList.toggle('open')};
setInterval(()=>{$('clock').textContent=new Date().toLocaleString('es-PE',{dateStyle:'medium',timeStyle:'medium'})},1000);
renderDepartments();seedDemoExits();render();