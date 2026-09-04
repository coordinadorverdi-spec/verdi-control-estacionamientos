const vehicles={
 'ABC-123':{owner:'Residente Demo',space:'A-01'},
 'VER-001':{owner:'Residente Verdi',space:'B-12'},
 'XYZ-789':{owner:'Visitante autorizado',space:'VIS-01'}
};
let logs=JSON.parse(localStorage.getItem('verdi_logs')||'[]');
let insideState=JSON.parse(localStorage.getItem('verdi_inside')||'{}');
const $=id=>document.getElementById(id);
function now(){return new Date().toLocaleTimeString('es-PE',{hour:'2-digit',minute:'2-digit'})}
function today(){return new Date().toLocaleDateString('es-PE')}
function render(){
 $('inside').textContent=Object.values(insideState).filter(Boolean).length;
 $('events').textContent=logs.filter(x=>x.date===today()).length;
 $('authorized').textContent=Object.keys(vehicles).length;
 $('history').innerHTML=logs.slice(0,12).map(x=>`<tr><td>${x.time}</td><td><b>${x.plate}</b></td><td>${x.owner}</td><td>${x.type==='entry'?'Entrada':x.type==='exit'?'Salida':'Denegado'}</td><td><span class="badge ${x.type==='entry'?'in':x.type==='exit'?'out':'deny'}">${x.authorized?'AUTORIZADO':'RECHAZADO'}</span></td></tr>`).join('')||'<tr><td colspan="5">Sin movimientos registrados.</td></tr>';
 localStorage.setItem('verdi_logs',JSON.stringify(logs));localStorage.setItem('verdi_inside',JSON.stringify(insideState));
}
function lookup(){
 const plate=$('plate').value.trim().toUpperCase(); $('plate').value=plate;
 const v=vehicles[plate]; const info=$('vehicleInfo');
 if(!v){info.classList.remove('hidden');info.innerHTML='<b>⚠ Vehículo no registrado</b><br>El acceso será rechazado.';$('entryBtn').disabled=true;$('exitBtn').disabled=true;return null}
 info.classList.remove('hidden');info.innerHTML=`<b>${v.owner}</b><br>Estacionamiento: ${v.space}<br>Estado: ${insideState[plate]?'🟢 Dentro':'⚪ Fuera'}`;
 $('entryBtn').disabled=!!insideState[plate]; $('exitBtn').disabled=!insideState[plate]; return v;
}
function movement(type){
 const plate=$('plate').value.trim().toUpperCase(),v=vehicles[plate];
 if(!v){logs.unshift({plate,owner:'No registrado',type:'denied',authorized:false,time:now(),date:today()});$('message').textContent='⛔ ACCESO RECHAZADO';render();return}
 insideState[plate]=type==='entry'; logs.unshift({plate,owner:v.owner,type,authorized:true,time:now(),date:today()});
 $('message').textContent=type==='entry'?'✅ ENTRADA REGISTRADA':'✅ SALIDA REGISTRADA'; lookup();render();
}
$('searchBtn').onclick=lookup;$('entryBtn').onclick=()=>movement('entry');$('exitBtn').onclick=()=>movement('exit');
$('plate').addEventListener('keydown',e=>{if(e.key==='Enter')lookup()});
$('plate').addEventListener('input',()=>{$('message').textContent=''});
$('clearBtn').onclick=()=>{if(confirm('¿Borrar los movimientos de prueba?')){logs=[];insideState={};render();lookup()}};
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{$('plate').value=b.dataset.plate;lookup()});
setInterval(()=>{$('clock').textContent=new Date().toLocaleString('es-PE',{dateStyle:'medium',timeStyle:'medium'})},1000);render();