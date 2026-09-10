from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v15 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v15 -->
<script>
(function(){
  const escv=x=>String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const dept=x=>deptCode(x);
  const park=v=>String(v?.authorized_parking_spaces||'').trim()||'—';
  const bas=v=>v?.parking_basement||((park(v).split(',')[0]&&typeof basementFor==='function')?basementFor(park(v).split(',')[0]):'—');
  const currentEvent=v=>events.filter(e=>e.vehicle_id===v.id).slice(-1)[0];
  const isInside=v=>{const e=currentEvent(v);return e?.movement==='entrada'};
  const frequent=v=>!!v.is_frequent;

  function renderV15(){
    // DENTRO: all newly registered vehicles are visible immediately when an entry event exists.
    const il=$('insideList');
    if(il) il.innerHTML=vehicles.filter(v=>!frequent(v)&&isInside(v)).map(v=>`<div class="row in"><span><b>${escv(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${dept(v.department_id)} · ${park(v)} ${bas(v)}</span><button class="btn" onclick="move('salida','${v.id}')">SALIÓ</button></div>`).join('')||'No hay vehículos dentro.';

    // SALIERON: only vehicles whose latest movement is salida remain here. ENTRÓ moves them out of this list.
    const outs=vehicles.map(v=>({v,e:currentEvent(v)})).filter(x=>x.e?.movement==='salida').sort((a,b)=>new Date(b.e.event_time)-new Date(a.e.event_time)).slice(0,50);
    const rl=$('recentList');
    if(rl) rl.innerHTML=outs.map(x=>`<div class="row out"><span><b>${escv(x.v.plate||x.v.code_label)}</b> · ${typeName(x.v.vehicle_type)}<br>D. ${dept(x.v.department_id)} · ${park(x.v)} ${bas(x.v)}</span><button class="btn" onclick="move('entrada','${x.v.id}')">ENTRÓ</button></div>`).join('')||'No hay vehículos que hayan salido.';

    // FRECUENTES: dedicated list, with edit and delete. They are not shown in Base.
    const vl=$('visitList');
    if(vl) vl.innerHTML=vehicles.filter(frequent).map(v=>`<div class="row"><span><b>${escv(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${dept(v.department_id)} · ${escv(v.responsible_name||'—')} · ${relName(v.relationship)}</span><span style="display:flex;gap:6px;width:100%;max-width:210px"><button class="btn" onclick="editFrequent('${v.id}')">EDITAR</button><button class="btn danger" onclick="deleteFrequent('${v.id}')">ELIMINAR</button></span></div>`).join('')||'No hay visitas frecuentes.';

    renderBaseV15();
    renderFindV15();
  }

  function renderBaseV15(){
    const box=$('baseList'); if(!box)return;
    const q=String($('finder')?.value||'').trim().toLowerCase();
    const mode=window.__verdiBaseSort||'dept';
    let list=vehicles.filter(v=>!frequent(v));
    if(q) list=list.filter(v=>[v.plate,v.code_label,dept(v.department_id)].filter(Boolean).join(' ').toLowerCase().includes(q));
    list.sort((a,b)=>{const aa=mode==='parking'?parseInt(park(a),10)||9999:parseInt(dept(a.department_id),10)||9999;const bb=mode==='parking'?parseInt(park(b),10)||9999:parseInt(dept(b.department_id),10)||9999;return aa-bb || String(a.plate||'').localeCompare(String(b.plate||''))});
    box.innerHTML=list.map(v=>`<div class="row"><span><b>${escv(v.plate||v.code_label)}</b> · Dpto. ${escv(dept(v.department_id))} · Cochera ${escv(park(v))} · ${escv(bas(v))}<br>Encargado: ${escv(v.responsible_name||'—')} · ${escv(relName(v.relationship))}</span></div>`).join('')||'No hay registros.';
  }
  function renderFindV15(){
    const box=$('findList'); if(!box)return;
    const q=String($('finder')?.value||'').trim().toLowerCase();
    let list=vehicles.filter(v=>!frequent(v));
    if(q) list=list.filter(v=>[v.plate,v.code_label,dept(v.department_id)].filter(Boolean).join(' ').toLowerCase().includes(q));
    box.innerHTML=list.slice(0,100).map(v=>`<div class="row"><span><b>${escv(v.plate||v.code_label)}</b> · Dpto. ${escv(dept(v.department_id))} · Cochera ${escv(park(v))} · ${escv(bas(v))}<br>Encargado: ${escv(v.responsible_name||'—')} · ${escv(relName(v.relationship))}</span></div>`).join('')||'No se encontraron registros.';
  }

  window.editFrequent=async function(id){
    const v=vehicles.find(x=>x.id===id); if(!v)return;
    const plate=prompt('Placa / código:',v.plate||v.code_label||''); if(plate===null)return;
    const person=prompt('Encargado / responsable:',v.responsible_name||''); if(person===null)return;
    const d=prompt('Dpto.:',dept(v.department_id)||''); if(d===null)return;
    const rel=prompt('Relación (propietario_dpto, inquilino_dpto, propietario_cochera, inquilino_externo, visita):',v.relationship||'visita'); if(rel===null)return;
    const did=await findDept(d);
    const r=await sb.from('vehicles').update({plate:plate.trim().toUpperCase(),code_label:plate.trim().toUpperCase(),responsible_name:person.trim()||null,department_id:did,relationship:rel,is_frequent:true}).eq('id',id).eq('building_id',BUILDING_ID);
    if(r.error){setMsg('msg','No se pudo editar: '+r.error.message);return}
    await load();
  };
  window.deleteFrequent=async function(id){
    const v=vehicles.find(x=>x.id===id); if(!v)return;
    if(!confirm('¿Eliminar esta visita frecuente de la lista de Frecuentes?'))return;
    const r=await sb.from('vehicles').update({is_frequent:false}).eq('id',id).eq('building_id',BUILDING_ID);
    if(r.error){setMsg('msg','No se pudo eliminar: '+r.error.message);return}
    await load();
  };

  // Ensure ENTRÓ creates the movement and the record immediately disappears from SALIERON.
  const oldMove=window.move;
  window.move=async function(action,id){
    await oldMove(action,id);
    if(action==='entrada'||action==='salida'){
      await load();
    }
  };

  // Prevent frequent vehicles from being shown in DENTRO/Base while keeping their dedicated control.
  const oldRender=window.render;
  window.render=function(){try{oldRender()}catch(e){} renderV15()};

  // Base sorting/filtering controls.
  const find=$('find');
  if(find && !document.getElementById('baseControls')){
    const controls=document.createElement('div');controls.id='baseControls';controls.style='display:flex;gap:6px;margin:8px 0;';
    controls.innerHTML='<button class="btn" id="sortDept">ORDENAR POR DPTO.</button><button class="btn" id="sortPark">ORDENAR POR COCHERA</button>';
    $('finder').insertAdjacentElement('afterend',controls);
    $('finder').addEventListener('input',function(){renderFindV15();renderBaseV15()});
    $('sortDept').onclick=function(){window.__verdiBaseSort='dept';renderBaseV15()};
    $('sortPark').onclick=function(){window.__verdiBaseSort='parking';renderBaseV15()};
  }

  // Replace temporary-rental form with explicit plate + rented parking + user department.
  const temp=$('temp');
  if(temp && !document.getElementById('tplate')){
    const grid=temp.querySelector('.grid');
    if(grid){grid.innerHTML='<input id="tplate" placeholder="Placa / código"><input id="tspace" type="number" placeholder="Cochera alquilada"><input id="tname" placeholder="Persona usuaria"><input id="tdept" list="depts" placeholder="Dpto. usuario"><input id="tfrom" type="date"><input id="tto" type="date">'}
    const old=$('tsave'); if(old)old.onclick=async function(){
      try{
        const plate=String($('tplate').value||'').trim().toUpperCase(), num=parseInt($('tspace').value,10), name=String($('tname').value||'').trim(), did=await findDept($('tdept').value), from=$('tfrom').value,to=$('tto').value;
        if(!plate||!Number.isFinite(num)||!did||!from||!to){setMsg('tmsg','Complete placa, cochera, Dpto. usuario y fechas.');return}
        const ps=spaces.find(x=>Number(x.space_number)===num); if(!ps){setMsg('tmsg','La cochera indicada no existe.');return}
        let v=vehicles.find(x=>String(x.plate||x.code_label).toUpperCase()===plate);
        if(v){const u=await sb.from('vehicles').update({department_id:did,parking_space_id:ps.id,authorized_parking_spaces:String(num),parking_basement:ps.basement,parking_required:true,responsible_name:name||v.responsible_name,relationship:'inquilino_dpto'}).eq('id',v.id);if(u.error)throw u.error}
        else{const ins=await sb.from('vehicles').insert({plate,code_label:plate,responsible_name:name||null,relationship:'inquilino_dpto',vehicle_type:'auto',department_id:did,parking_space_id:ps.id,authorized_parking_spaces:String(num),parking_basement:ps.basement,parking_required:true,building_id:BUILDING_ID}).select().single();if(ins.error)throw ins.error;v=ins.data}
        const r=await sb.from('temporary_parking_rentals').insert({vehicle_id:v.id,parking_space_id:ps.id,user_department_id:did,occupant_name:name||null,occupant_role:'usuario_dpto',start_date:from,end_date:to,active:true,building_id:BUILDING_ID});if(r.error)throw r.error;
        setMsg('tmsg','Alquiler temporal registrado correctamente.',true);await load();
      }catch(e){setMsg('tmsg','Error: '+(e.message||e))}
    };
  }

  // Re-run the corrected view after load/render cycles.
  setTimeout(()=>{try{renderV15()}catch(e){}},300);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
