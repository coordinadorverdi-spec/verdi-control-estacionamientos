from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v7 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v7 -->
<script>
(function(){
  const nrm=x=>String(x??'').trim().toUpperCase();
  const norm=x=>nrm(x).replace(/\s+/g,'');
  const vehicleForEvent=e=>(vehicles||[]).find(v=>v.id===e?.vehicle_id)||null;
  const uniqueVehicles=list=>{const seen=new Set();return (list||[]).filter(v=>{const k=norm(v?.plate||v?.code_label);if(!k||seen.has(k))return false;seen.add(k);return true})};
  const eventParking=e=>{if(e?.parking_space_id){const p=(spaces||[]).find(x=>x.id===e.parking_space_id);if(p)return {n:p.space_number,s:p.basement||'—'}}return null};
  const vehicleParking=v=>{if(!v)return null;const raw=String(v.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean)[0];if(raw){const n=parseInt(raw,10);return {n:raw,s:n>=1&&n<=43?'S1':n<=89?'S2':n<=136?'S3':n<=147?'S4':'—'}}if(v.parking_space_id){const p=(spaces||[]).find(x=>x.id===v.parking_space_id);if(p)return {n:p.space_number,s:p.basement||'—'}}return null};
  const displayParking=(v,e)=>vehicleParking(v)||eventParking(e);

  async function purgeExpiredDeletedHistory(){
    const cutoff=new Date();cutoff.setMonth(cutoff.getMonth()-1);
    const r=await sb.from('access_events').delete().not('deleted_at','is',null).lt('deleted_at',cutoff.toISOString()).eq('building_id',BUILDING_ID);
    if(r.error)console.warn('Depuración de permanencias:',r.error.message);
  }

  const oldLoad=window.load;
  window.load=async function(){
    try{await purgeExpiredDeletedHistory()}catch(e){console.warn('Depuración histórica:',e)}
    return oldLoad();
  };

  window.deleteVehicleFromBase=async function(id){
    if(!canAdmin()){setMsg('msg','Solo Administración puede eliminar placas.');return}
    const v=(vehicles||[]).find(x=>x.id===id);if(!v){setMsg('msg','No se encontró la placa.');return}
    const plate=nrm(v.plate||v.code_label);
    if(!confirm('¿Eliminar la placa '+plate+' de la base activa?\n\nLa cochera quedará libre. El vehículo desaparecerá de DENTRO y SALIERON. El historial de PERMANENCIAS se conservará durante 1 mes.'))return;
    try{
      const now=new Date().toISOString();
      let r=await sb.from('access_events').update({deleted_at:now}).eq('vehicle_id',id).eq('building_id',BUILDING_ID);
      if(r.error)throw r.error;
      await sb.from('vehicle_parking_spaces').update({active:false}).eq('vehicle_id',id);
      await audit('ELIMINAR','vehicle',{id,plate,deleted_at:now,history_retention:'1 mes'});
      r=await sb.from('vehicles').delete().eq('id',id).eq('building_id',BUILDING_ID);
      if(r.error)throw r.error;
      setMsg('msg','Placa '+plate+' eliminada. Cochera liberada y permanencias conservadas por 1 mes.',true);
      await load();
    }catch(e){console.error('Eliminar placa:',e);setMsg('msg','No se pudo eliminar la placa: '+(e.message||e))}
  };

  const oldRender=window.render;
  window.render=function(){
    oldRender();
    const q=norm($('finder')?.value);
    const base=$('baseList');
    if(base){
      base.innerHTML=uniqueVehicles(vehicles).filter(v=>!q||[v.plate,v.code_label,deptCode(v.department_id),v.responsible_name,v.authorized_parking_spaces].filter(Boolean).join(' ').toUpperCase().includes(q)).map(v=>'<div class="row"><span><b>'+esc(nrm(v.plate||v.code_label))+'</b> · '+typeName(v.vehicle_type)+'<br>'+esc(v.responsible_name||'—')+' · '+relName(v.relationship)+' · Dpto. '+deptCode(v.department_id)+'</span>'+(canAdmin()?'<button class="btn danger" style="width:auto;flex:0 0 auto" onclick="deleteVehicleFromBase(\''+v.id+'\')">Eliminar</button>':'')+'</div>').join('')||'Base vacía.';
    }

    // SALIERON es solo operación activa: los eventos cuyo vehículo fue eliminado quedan únicamente en PERMANENCIAS.
    const rq=norm($('recentFilter')?.value);
    const seen=new Set();
    const outs=(events||[]).filter(e=>e.movement==='salida').slice().reverse().filter(e=>{
      const v=vehicleForEvent(e),k=norm(e.plate||v?.plate||v?.code_label);
      if(!v||!k||seen.has(k))return false;
      if(rq&&![e.plate,v.plate,v.code_label,deptCode(e.department_id||v.department_id),v.authorized_parking_spaces].filter(Boolean).join(' ').toUpperCase().includes(rq))return false;
      seen.add(k);return true;
    }).slice(0,100);
    const rl=$('recentList');
    if(rl){
      rl.innerHTML=outs.map(e=>{const v=vehicleForEvent(e),p=displayParking(v,e),label=nrm(e.plate||v.plate||v.code_label)||'—';return '<div class="row out compact-row"><span><b>'+esc(label+' D. '+deptCode(e.department_id||v.department_id)+' - '+(p?p.n:'—')+' '+(p?p.s:'—'))+'</b></span><button class="btn primary" style="width:auto" onclick="registerEntryFromExit(\''+e.id+'\')">[E]</button></div>'}).join('')||'No hay salidas que coincidan.';
    }

    const hist=(events||[]).slice().reverse().filter(e=>{
      const v=vehicleForEvent(e),dq=norm($('histDept')?.value),pq=norm($('histPlate')?.value),d=norm(deptCode(e.department_id||v?.department_id)),plate=norm(e.plate||v?.plate||v?.code_label);
      return (!dq||d.includes(dq))&&(!pq||plate===pq);
    });
    const hl=$('histList');
    if(hl)hl.innerHTML=hist.map(e=>{
      const v=vehicleForEvent(e),p=displayParking(v,e),actions=canAdmin()?'<button class="btn" style="width:auto;margin-right:4px" onclick="editAccessEvent(\''+e.id+'\')">Editar</button><button class="btn danger" style="width:auto" onclick="deleteAccessEvent(\''+e.id+'\')">Eliminar</button>':'';
      return '<tr><td>'+esc(deptCode(e.department_id||v?.department_id))+'</td><td>'+esc(nrm(e.plate||v?.plate||v?.code_label))+'</td><td>'+typeName(e.vehicle_type||v?.vehicle_type)+'</td><td>'+esc(e.movement||'')+'</td><td>'+new Date(e.event_time).toLocaleString('es-PE')+'</td><td>'+esc(p?('Cochera '+p.n+' — '+p.s):'—')+'</td><td>'+actions+'</td></tr>';
    }).join('');
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
