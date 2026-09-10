from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
marker = '<!-- Verdi UI correction patch v4 -->'
if marker in s:
    raise SystemExit(0)
patch = r'''<!-- Verdi UI correction patch v4 -->
<script>
(function(){
  const basementFor=x=>{const n=parseInt(String(x??'').trim(),10);if(n>=1&&n<=43)return'S1';if(n>=44&&n<=89)return'S2';if(n>=90&&n<=136)return'S3';if(n>=137&&n<=147)return'S4';return'—'};
  const norm=x=>String(x??'').trim().toLowerCase();
  const eventVehicle=e=>(vehicles||[]).find(v=>v.id===e?.vehicle_id)||null;
  const parkingEntries=v=>{
    const out=[];
    String(v?.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean).forEach(x=>out.push({number:x,basement:basementFor(x)}));
    (Array.isArray(v?._linkedParking)?v._linkedParking:[]).forEach(x=>{if(!out.some(y=>String(y.number)===String(x.number)))out.push(x)});
    if(!out.length&&v?.parking_space_id){const p=(spaces||[]).find(x=>x.id===v.parking_space_id);if(p)out.push({number:p.space_number,basement:p.basement||basementFor(p.space_number)})}
    return out;
  };
  const eventParking=e=>{
    if(e?.parking_space_id){const p=(spaces||[]).find(x=>x.id===e.parking_space_id);if(p)return [{number:p.space_number,basement:p.basement||basementFor(p.space_number)}]}
    return [];
  };
  const parkingList=(v,e)=>{const a=[...parkingEntries(v||{}),...eventParking(e||{})];const seen=new Set();const z=a.filter(x=>{const k=String(x.number);if(seen.has(k))return false;seen.add(k);return true});return z.length?z.map(x=>'Cochera '+esc(x.number)+' — '+esc(x.basement||basementFor(x.number))).join('<br>'):'Cochera no registrada'};

  async function loadLinkedParking(){
    (vehicles||[]).forEach(v=>v._linkedParking=[]);
    const r=await sb.from('vehicle_parking_spaces').select('vehicle_id,parking_space_id,active').eq('building_id',BUILDING_ID).eq('active',true);
    if(r.error){console.warn('Cocheras vinculadas:',r.error.message);return}
    (r.data||[]).forEach(x=>{const v=(vehicles||[]).find(y=>y.id===x.vehicle_id),p=(spaces||[]).find(y=>y.id===x.parking_space_id);if(v&&p)v._linkedParking.push({number:p.space_number,basement:p.basement||basementFor(p.space_number)})});
  }
  const oldLoad=window.load;
  window.load=async function(){await oldLoad();await loadLinkedParking();window.render()};

  async function saveParking(v,raw){
    if(!v)return;
    const clean=String(raw??'').split(',').map(x=>x.trim()).filter(Boolean).join(',');
    if(!clean)return;
    const nums=clean.split(',').map(x=>parseInt(x,10)).filter(Number.isFinite);
    const first=nums[0];
    const ps=(spaces||[]).find(x=>Number(x.space_number)===first);
    const data={authorized_parking_spaces:clean,parking_basement:first?basementFor(first):null,parking_required:true};
    if(ps)data.parking_space_id=ps.id;
    const r=await sb.from('vehicles').update(data).eq('id',v.id).eq('building_id',BUILDING_ID);
    if(r.error)throw r.error;
    v.authorized_parking_spaces=clean;v.parking_basement=data.parking_basement;v.parking_required=true;if(ps)v.parking_space_id=ps.id;
  }

  window.registerEntryFromExit=async function(id){
    try{
      const e=(events||[]).find(x=>x.id===id);if(!e){setMsg('msg','No se encontró la salida seleccionada.');return}
      const v=eventVehicle(e);
      if(!v){setMsg('msg','La salida no tiene un vehículo asociado.');return}
      if(inside(v)){setMsg('msg','Este vehículo ya figura DENTRO.');return}
      const ps=parkingEntries(v)[0];
      const ins={vehicle_id:v.id,visitor_id:null,department_id:e.department_id||v.department_id||null,person_id:v.person_id||null,plate:e.plate||v.plate||v.code_label||null,vehicle_type:e.vehicle_type||v.vehicle_type||null,description:e.description||v.description||null,worker_name:user?.email||profile?.email||null,movement:'entrada',source_type:'manual',building_id:BUILDING_ID};
      if(ps){const p=(spaces||[]).find(x=>String(x.space_number)===String(ps.number));if(p)ins.parking_space_id=p.id}
      const r=await sb.from('access_events').insert(ins).select().single();if(r.error)throw r.error;
      if(typeof audit==='function')await audit('CREAR','access_event',{id:r.data?.id||null,plate:ins.plate,movement:'entrada',from_exit:id});
      await load();setMsg('msg','Entrada registrada correctamente.',true);
    }catch(err){console.error(err);setMsg('msg','No se pudo registrar el ingreso: '+(err.message||err))}
  };

  const oldMove=window.move;
  window.move=async function(action,id){
    const raw=String($('code')?.value||'').trim().toUpperCase();
    const enteredParking=String($('spaces')?.value||'').trim();
    if(action==='entrada'&&id){const v=(vehicles||[]).find(x=>x.id===id);if(v&&enteredParking){try{await saveParking(v,enteredParking)}catch(err){setMsg('msg','No se pudo guardar la cochera: '+(err.message||err));return}}}
    await oldMove(action,id);
    if(action==='entrada'&&raw&&enteredParking){const v=(vehicles||[]).find(x=>String(x.plate||x.code_label||'').toUpperCase()===raw);if(v)try{await saveParking(v,enteredParking)}catch(err){console.warn('Cochera posterior:',err)}}
    await load();
  };

  const oldRender=window.render;
  window.render=function(){
    oldRender();
    const iq=norm($('insideFilter')?.value),rq=norm($('recentFilter')?.value);
    const il=$('insideList');if(il)il.innerHTML=(vehicles||[]).filter(inside).filter(v=>!iq||[v.plate,v.code_label,deptCode(v.department_id),v.authorized_parking_spaces].filter(Boolean).join(' ').toLowerCase().includes(iq)).map(v=>'<div class="row in"><span><b>'+esc(v.plate||v.code_label)+'</b> · '+typeName(v.vehicle_type)+'<br>Dpto. '+esc(deptCode(v.department_id))+'<br>'+parkingList(v,{})+'</span><button class="btn" onclick="move(\'salida\',\''+v.id+'\')">SALIÓ</button></div>').join('')||'No hay vehículos dentro.';
    const outs=(events||[]).filter(e=>e.movement==='salida').slice().reverse().filter(e=>{const v=eventVehicle(e);return !rq||[e.plate,v?.plate,v?.code_label,deptCode(e.department_id||v?.department_id),v?.authorized_parking_spaces].filter(Boolean).join(' ').toLowerCase().includes(rq)}).slice(0,100);
    const rl=$('recentList');if(rl)rl.innerHTML=outs.map(e=>{const v=eventVehicle(e);return '<div class="row out"><span><b>'+esc(e.plate||v?.plate||'—')+'</b> · '+typeName(e.vehicle_type||v?.vehicle_type)+'<br>Dpto. '+esc(deptCode(e.department_id||v?.department_id))+'<br>'+parkingList(v,e)+'<br>'+new Date(e.event_time).toLocaleString('es-PE')+'</span><button class="btn primary" style="width:auto" onclick="registerEntryFromExit(\''+e.id+'\')">ENTRÓ</button></div>'}).join('')||'No hay salidas que coincidan.';
    const hl=$('histList');if(hl)hl.innerHTML=(events||[]).slice().reverse().map(e=>{const v=eventVehicle(e),a=canAdmin()?'<button class="btn" style="width:auto;margin-right:4px" onclick="editAccessEvent(\''+e.id+'\')">Editar</button><button class="btn danger" style="width:auto" onclick="deleteAccessEvent(\''+e.id+'\')">Eliminar</button>':'';return '<tr><td>'+esc(deptCode(e.department_id||v?.department_id))+'</td><td>'+esc(e.plate||v?.plate||'—')+'</td><td>'+typeName(e.vehicle_type||v?.vehicle_type)+'</td><td>'+esc(e.movement||'')+'</td><td>'+new Date(e.event_time).toLocaleString('es-PE')+'</td><td>'+parkingList(v,e)+'</td><td>'+a+'</td></tr>'}).join('');
    const table=hl?.closest('table'),head=table?.querySelector('thead tr');if(head){const hs=[...head.querySelectorAll('th')];if(hs.length){const last=hs[hs.length-1];if(last.textContent.trim()==='Trabajador')last.textContent='Cochera / sótano';if(![...head.querySelectorAll('th')].some(x=>x.textContent.trim()==='Acciones')){const a=document.createElement('th');a.textContent='Acciones';head.appendChild(a)}}}
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
