from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = '<!-- Verdi UI correction patch v3 -->'
if marker in s:
    raise SystemExit(0)
patch = r'''<!-- Verdi UI correction patch v3 -->
<script>
(function(){
  const basementFor=x=>{const n=parseInt(String(x??'').trim(),10);if(n>=1&&n<=43)return'S1';if(n>=44&&n<=89)return'S2';if(n>=90&&n<=136)return'S3';if(n>=137&&n<=147)return'S4';return'—'};
  const linkedEntries=v=>Array.isArray(v?._linkedParking)?v._linkedParking:[];
  const parkingEntries=v=>{const out=[];String(v?.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean).forEach(x=>out.push({number:x,basement:basementFor(x)}));linkedEntries(v).forEach(x=>{if(!out.some(y=>String(y.number)===String(x.number)))out.push(x)});if(!out.length&&v?.parking_space_id){const p=(spaces||[]).find(x=>x.id===v.parking_space_id);if(p)out.push({number:p.space_number,basement:p.basement})}return out};
  const parkingList=v=>{const a=parkingEntries(v||{});return a.length?a.map(x=>'Cochera '+esc(x.number)+' — '+esc(x.basement||basementFor(x.number))).join('<br>'):'Cochera no registrada'};
  const vehicleForEvent=e=>(vehicles||[]).find(v=>v.id===e.vehicle_id)||null;
  const norm=x=>String(x??'').trim().toLowerCase();
  const vehicleMatches=(v,q)=>!q||[v?.plate,v?.code_label,deptCode(v?.department_id),v?.responsible_name,v?.authorized_parking_spaces].filter(Boolean).join(' ').toLowerCase().includes(q);
  const eventMatches=(e,q)=>{const v=vehicleForEvent(e);return !q||[e?.plate,v?.plate,deptCode(e?.department_id||v?.department_id),v?.authorized_parking_spaces].filter(Boolean).join(' ').toLowerCase().includes(q)};

  async function loadLinkedParking(){
    const r=await sb.from('vehicle_parking_spaces').select('vehicle_id,parking_space_id,active').eq('building_id',BUILDING_ID).eq('active',true);
    (vehicles||[]).forEach(v=>v._linkedParking=[]);
    if(r.error){console.warn(r.error);return}
    (r.data||[]).forEach(x=>{const v=(vehicles||[]).find(y=>y.id===x.vehicle_id),p=(spaces||[]).find(y=>y.id===x.parking_space_id);if(v&&p)v._linkedParking.push({number:p.space_number,basement:p.basement})});
  }
  const baseLoad=window.load;
  window.load=async function(){await baseLoad();await loadLinkedParking();window.render();};

  async function persistParking(v,raw){
    if(!v||!raw)return;
    const clean=String(raw).split(',').map(x=>x.trim()).filter(Boolean).join(',');if(!clean)return;
    const nums=clean.split(',').map(x=>parseInt(x,10)).filter(Number.isFinite);
    const r=await sb.from('vehicles').update({authorized_parking_spaces:clean,parking_basement:nums.length?basementFor(nums[0]):null,parking_required:true}).eq('id',v.id).eq('building_id',BUILDING_ID);
    if(r.error)throw r.error;
  }
  const baseMove=window.move;
  window.move=async function(action,id){
    const rawBefore=String($('code')?.value||'').trim().toUpperCase();
    const spacesBefore=String($('spaces')?.value||'').trim();
    if(action==='entrada'){
      let v=(vehicles||[]).find(x=>x.id===id)||null;if(!v&&rawBefore)v=(vehicles||[]).find(x=>String(x.plate||x.code_label||'').toUpperCase()===rawBefore);
      if(v&&spacesBefore){try{await persistParking(v,spacesBefore)}catch(err){console.error(err);setMsg('msg','No se pudo guardar la cochera: '+(err.message||err));return}}
    }
    await baseMove(action,id);
    if(action==='entrada'&&rawBefore){const v=(vehicles||[]).find(x=>String(x.plate||x.code_label||'').toUpperCase()===rawBefore);if(v&&spacesBefore)try{await persistParking(v,spacesBefore)}catch(err){console.error(err)}}
    await load();
  };

  window.registerEntryFromExit=async id=>{if(id)await window.move('entrada',id)};

  window.editAccessEvent=async function(id){
    if(!canAdmin()){setMsg('msg','Solo Master/Admin puede editar permanencias.');return}
    const e=(events||[]).find(x=>x.id===id);if(!e)return;
    const v=vehicleForEvent(e);
    const plate=prompt('Placa / código:',e.plate||v?.plate||'');if(plate===null)return;
    const newPlate=plate.trim().toUpperCase();if(!newPlate){alert('La placa/código no puede quedar vacío.');return}
    const oldDept=deptCode(e.department_id||v?.department_id);const dept=prompt('Dpto. asociado:',oldDept==='—'?'':oldDept);if(dept===null)return;
    const dq=String(dept).trim().toUpperCase().replace(/^DPTO\.?\s*/,'');let department_id=null;
    if(dq){const d=(depts||[]).find(x=>String(x.code||'').toUpperCase()===dq);if(!d){alert('Dpto. no encontrado: '+dq);return}department_id=d.id}
    try{const r=await sb.from('access_events').update({plate:newPlate,department_id}).eq('id',id).eq('building_id',BUILDING_ID);if(r.error)throw r.error;if(typeof audit==='function')await audit('EDITAR','access_event',{id,plate:newPlate,department_id});await load()}catch(err){console.error(err);setMsg('msg','No se pudo editar: '+(err.message||err))}
  };
  window.deleteAccessEvent=async function(id){if(!canAdmin()){setMsg('msg','Solo Master/Admin puede eliminar permanencias.');return}const e=(events||[]).find(x=>x.id===id);if(!e)return;if(!confirm('¿Eliminar esta permanencia?\n'+(e.plate||'—')+' · '+e.movement))return;try{const r=await sb.from('access_events').delete().eq('id',id).eq('building_id',BUILDING_ID);if(r.error)throw r.error;if(typeof audit==='function')await audit('ELIMINAR','access_event',{id,plate:e.plate||null,movement:e.movement||null});await load()}catch(err){console.error(err);setMsg('msg','No se pudo eliminar: '+(err.message||err))}};

  function filterInput(section,id,placeholder){const s=$(section);if(!s)return null;let i=$(id);if(!i){i=document.createElement('input');i.id=id;i.placeholder=placeholder;i.autocomplete='off';s.querySelector('h2')?.after(i)}return i}
  const insideFilter=filterInput('inside','insideFilter','Buscar por placa o Dpto.');const recentFilter=filterInput('recent','recentFilter','Buscar por placa o Dpto.');
  const baseRender=window.render;
  window.render=function(){
    baseRender();
    const iq=norm(insideFilter?.value),rq=norm(recentFilter?.value);
    const il=$('insideList');if(il)il.innerHTML=(vehicles||[]).filter(inside).filter(v=>vehicleMatches(v,iq)).map(v=>'<div class="row in"><span><b>'+esc(v.plate||v.code_label)+'</b> · '+typeName(v.vehicle_type)+'<br>'+parkingList(v)+'</span><button class="btn" onclick="move(\'salida\',\''+v.id+'\')">SALIÓ</button></div>').join('')||'No hay vehículos que coincidan.';
    const outs=(events||[]).filter(e=>e.movement==='salida').slice().reverse().filter(e=>eventMatches(e,rq)).slice(0,100);const rl=$('recentList');if(rl)rl.innerHTML=outs.map(e=>{const v=vehicleForEvent(e);return '<div class="row out"><span><b>'+esc(e.plate||v?.plate||'—')+'</b> · '+typeName(e.vehicle_type||v?.vehicle_type)+'<br>'+parkingList(v||{})+'<br>'+new Date(e.event_time).toLocaleString('es-PE')+'</span><button class="btn primary" style="width:auto" onclick="registerEntryFromExit(\''+(v?.id||e.vehicle_id||'')+'\')">ENTRÓ</button></div>'}).join('')||'No hay salidas que coincidan.';
    const hl=$('histList');if(hl)hl.innerHTML=(events||[]).slice().reverse().map(e=>{const v=vehicleForEvent(e),a=canAdmin()?'<button class="btn" style="width:auto;margin-right:4px" onclick="editAccessEvent(\''+e.id+'\')">Editar</button><button class="btn danger" style="width:auto" onclick="deleteAccessEvent(\''+e.id+'\')">Eliminar</button>':'';return '<tr><td>'+deptCode(e.department_id||v?.department_id)+'</td><td>'+esc(e.plate||v?.plate||'—')+'</td><td>'+typeName(e.vehicle_type||v?.vehicle_type)+'</td><td>'+esc(e.movement||'')+'</td><td>'+new Date(e.event_time).toLocaleString('es-PE')+'</td><td>'+parkingList(v||{})+'</td><td>'+a+'</td></tr>'}).join('');
  };
  const hl=$('histList'),table=hl?.closest('table'),head=table?.querySelector('thead tr');if(head&&!head.querySelector('[data-v3-parking]')){const h=document.createElement('th');h.textContent='Cochera / sótano';h.dataset.v3Parking='1';head.appendChild(h);const a=document.createElement('th');a.textContent='Acciones';head.appendChild(a)}
  [insideFilter,recentFilter].forEach(i=>i&&i.addEventListener('input',()=>window.render()));
  const finder=$('finder');if(finder)finder.addEventListener('input',function(){const q=norm(this.value),out=$('findList');if(out)out.innerHTML=(vehicles||[]).filter(v=>vehicleMatches(v,q)).map(v=>'<div class="row"><span><b>'+esc(v.plate||v.code_label)+'</b> · '+typeName(v.vehicle_type)+'<br>'+esc(v.responsible_name||'—')+' · '+relName(v.relationship)+' · Dpto. '+deptCode(v.department_id)+'<br>'+parkingList(v)+'</span></div>').join('')||'Sin resultados.'});
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
