const baseVehicles={
 'ABC-123':{owner:'Residente Demo',dept:'101',spaces:['1'],type:'auto'},
 'VER-001':{owner:'Residente Verdi',dept:'205',spaces:['45','46'],type:'auto'},
 'XYZ-789':{owner:'Visitante autorizado',dept:'1204',spaces:[],type:'auto'}
};
let vehicles=JSON.parse(localStorage.getItem('verdi_vehicles')||'null')||baseVehicles;
let logs=JSON.parse(localStorage.getItem('verdi_logs')||'[]');
let insideState=JSON.parse(localStorage.getItem('verdi_inside')||'{}');
let selectedPlate='';
const $=id=>document.getElementById(id);
function now(){return new Date().toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
function today(){return new Date().toLocaleDateString('es-PE')}
function basement(n){n=Number(n);return n>=1&&n<=43?'S1':n<=89?'S2':n<=136?'S3':n<=147?'S4':'—'}
function spaceText(v){return v.spaces&&v.spaces.length?v.spaces.map(n=>`${n} (${basement(n)})`).join(', '):'Sin cochera asignada'}
function departments(){const a=[];a.push('101','102','103');for(let floor=2;floor<=15;floor++)for(let n=1;n<=9;n++)a.push(`${floor}${String(n).padStart(2,'0')}`);return a}
function renderDepartments(){ $('department').innerHTML='<option value="">Seleccione Dpto.</option>'+departments().map(d=>`<option value="${d}">${d}</option>`).join('') }
function save(){localStorage.setItem('verdi_vehicles',JSON.stringify(vehicles));localStorage.setItem('verdi_logs',JSON.stringify(logs));localStorage.setItem('verdi_inside',JSON.stringify(insideState))}
function buildHistory(){
 const rows=[]; const open={};
 [...logs].reverse().forEach(x=>{
  if(x.type==='entry'){
   const row={plate:x.plate,dept:x.dept||'—',owner:x.owner||'—',spaces:x.spaces||'—',entryDate:x.date||'—',entryTime:x.time||'—',exitDate:'—',exitTime:'—',status:'DENTRO'};
   rows.push(row); open[x.plate]=row;
  } else if(x.type==='exit') {
   const row=open[x.plate];
   if(row){row.exitDate=x.date||'—';row.exitTime=x.time||'—';row.status='FUERA';delete open[x.plate]}
   else rows.push({plate:x.plate,dept:x.dept||'—',owner:x.owner||'—',spaces:x.spaces||'—',entryDate:'—',entryTime:'—',exitDate:x.date||'—',exitTime:x.time||'—',status:'FUERA'});
  }
 });
 return rows.reverse();
}
function render(){
 $('inside').textContent=Object.values(insideState).filter(Boolean).length;
 $('events').textContent=logs.filter(x=>x.date===today()).length;
 $('authorized').textContent=Object.keys(vehicles).length;
 const rows=buildHistory();
 $('history').innerHTML=rows.slice(0,50).map(x=>`<tr><td><b>${x.dept}</b></td><td><b>${x.plate}</b><br><small>${x.owner}</small></td><td>${x.entryDate}<br><b>${x.entryTime}</b></td><td>${x.exitDate}<br><b>${x.exitTime}</b></td><td>${x.spaces}</td><td><span class="badge ${x.status==='DENTRO'?'in':'out'}">${x.status}</span></td></tr>`).join('')||'<tr><td colspan="6">Sin movimientos registrados.</td></tr>';
 save();
}
function showVehicle(plate){
 selectedPlate=plate; const v=vehicles[plate]; const info=$('vehicleInfo');
 $('newVehicle').classList.add('hidden');
 if(!v){info.classList.remove('hidden');info.innerHTML='<b>⚠ Placa no registrada</b><br>Si se visualiza al residente, complete el registro rápido abajo.';$('entryBtn').disabled=true;$('exitBtn').disabled=true;prepareNew();return null}
 info.classList.remove('hidden');info.innerHTML=`<div class="vehicle-main"><b>${v.owner}</b><strong>Dpto. ${v.dept}</strong></div><div>🚗 ${v.type} &nbsp; · &nbsp; 🅿️ Cocheras: <b>${spaceText(v)}</b></div><div>Estado: <b>${insideState[plate]?'🟢 DENTRO':'⚪ FUERA'}</b></div>`;
 $('entryBtn').disabled=!!insideState[plate];$('exitBtn').disabled=!insideState[plate];return v;
}
function prepareNew(){ $('newVehicle').classList.remove('hidden');$('newDept').value=$('department').value||'';$('newOwner').focus(); }
function searchPlate(){showVehicle($('plate').value.trim().toUpperCase())}
function searchDept(){
 const dept=$('department').value;const box=$('deptCars');if(!dept){box.innerHTML='';return}
 const list=Object.entries(vehicles).filter(([,v])=>v.dept===dept);box.innerHTML=list.length?`<div class="dept-title">Vehículos de Dpto. ${dept}</div>`+list.map(([plate,v])=>`<div class="car-row"><div><b>${plate}</b><br><span>${v.owner} · 🅿️ ${spaceText(v)} · ${insideState[plate]?'🟢 DENTRO':'⚪ FUERA'}</span></div><button class="quick ${insideState[plate]?'quick-out':'quick-in'}" data-quick="${plate}" data-action="${insideState[plate]?'exit':'entry'}">${insideState[plate]?'SALIÓ':'ENTRÓ'}</button></div>`).join(''):'<div class="empty">No hay vehículos registrados para este Dpto. Puede registrar una nueva placa al ingresar.</div>';
 box.querySelectorAll('[data-quick]').forEach(b=>b.onclick=()=>{selectedPlate=b.dataset.quick;$('plate').value=selectedPlate;showVehicle(selectedPlate);movement(b.dataset.action)})
}
function movement(type){
 let plate=selectedPlate||$('plate').value.trim().toUpperCase();let v=vehicles[plate];
 if(!v){
  if(!$('registerVehicle').checked){$('message').textContent='⚠ Debe registrar la placa o cancelar el movimiento.';return}
  const owner=$('newOwner').value.trim(),dept=$('newDept').value.trim(),spaces=$('newSpaces').value.split(',').map(x=>x.trim()).filter(Boolean);
  if(!owner||!dept){$('message').textContent='⚠ Complete residente y Dpto. para registrar.';return}
  v=vehicles[plate]={owner,dept,spaces,type:$('newType').value};
 }
 if(type==='entry'&&insideState[plate]){ $('message').textContent='⚠ El vehículo ya figura DENTRO.';return }
 if(type==='exit'&&!insideState[plate]){ $('message').textContent='⚠ El vehículo ya figura FUERA.';return }
 insideState[plate]=type==='entry';logs.unshift({plate,owner:v.owner,dept:v.dept,spaces:spaceText(v),type,authorized:true,time:now(),date:today()});
 $('message').textContent=type==='entry'?'✅ ENTRADA REGISTRADA':'✅ SALIDA REGISTRADA';selectedPlate=plate;showVehicle(plate);render();if($('department').value)searchDept();
}
$('searchBtn').onclick=searchPlate;$('entryBtn').onclick=()=>movement('entry');$('exitBtn').onclick=()=>movement('exit');$('deptBtn').onclick=searchDept;$('department').onchange=searchDept;
$('plate').addEventListener('keydown',e=>{if(e.key==='Enter')searchPlate()});
$('plate').addEventListener('input',()=>{$('message').textContent='';selectedPlate=''});
$('clearBtn').onclick=()=>{if(confirm('¿Borrar movimientos y restaurar vehículos de demo?')){vehicles=JSON.parse(JSON.stringify(baseVehicles));logs=[];insideState={};save();render();showVehicle('')}};
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{$('plate').value=b.dataset.plate;searchPlate()});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');const mode=t.dataset.mode;$('plateSearch').classList.toggle('hidden',mode!=='plate');$('deptSearch').classList.toggle('hidden',mode!=='dept');$('vehicleInfo').classList.add('hidden');$('newVehicle').classList.add('hidden');$('message').textContent=''});
$('registerVehicle').onchange=()=>{};
setInterval(()=>{$('clock').textContent=new Date().toLocaleString('es-PE',{dateStyle:'medium',timeStyle:'medium'})},1000);
renderDepartments();render();