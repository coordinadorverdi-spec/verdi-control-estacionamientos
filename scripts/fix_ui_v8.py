from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v8 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v8 -->
<script>
(function(){
  const nrm=x=>String(x??'').trim().toUpperCase();
  const norm=x=>nrm(x).replace(/\s+/g,'');
  const platePattern=/^[A-Z0-9]{3}-[A-Z0-9]{3}$/;
  const special=new Set(['BICICLETA','PATIN','MOTO','BICIMOTO','TRIMOTO']);
  const vehicleForEvent=e=>(vehicles||[]).find(v=>v.id===e?.vehicle_id)||null;
  const parkingByNumber=n=>(spaces||[]).find(p=>String(p.space_number)===String(n));
  const basement=n=>{const x=parseInt(String(n??''),10);if(x>=1&&x<=43)return'S1';if(x<=89&&x>=44)return'S2';if(x<=136&&x>=90)return'S3';if(x<=147&&x>=137)return'S4';return'—'};
  const parkingOf=v=>{const raw=String(v?.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean)[0];if(raw)return {n:raw,s:basement(raw)};if(v?.parking_space_id){const p=spaces.find(x=>x.id===v.parking_space_id);if(p)return {n:p.space_number,s:p.basement||basement(p.space_number)}}return null};
  const parkingOfEvent=e=>{if(e?.parking_space_id){const p=spaces.find(x=>x.id===e.parking_space_id);if(p)return {n:p.space_number,s:p.basement||basement(p.space_number)}}return null};

  function normalizePlateValue(raw,kind){
    let x=nrm(raw).replace(/\s+/g,'');
    if(special.has(nrm(kind)) && !platePattern.test(x)) return nrm(kind);
    x=x.replace(/[^A-Z0-9-]/g,'');
    const al=x.replace(/-/g,'');
    if(al.length===6) x=al.slice(0,3)+'-'+al.slice(3);
    return x;
  }

  function setHistHeaders(){
    const tr=$('histList')?.closest('table')?.querySelector('thead tr');
    if(tr)tr.innerHTML='<th>Dpto.</th><th>Placa</th><th>Tipo</th><th>Movimiento</th><th>Fecha/hora</th><th>Cochera / sótano</th><th>Acciones</th>';
  }

  // Edición de PERMANENCIAS: placa, Dpto. y cochera son datos maestros; el movimiento y fecha/hora nunca se modifican.
  window.editAccessEvent=async function(id){
    if(!canAdmin()){setMsg('msg','Solo Administración puede editar permanencias.');return}
    const e=(events||[]).find(x=>x.id===id);if(!e){setMsg('msg','No se encontró el movimiento.');return}
    const v=vehicleForEvent(e);
    const currentPlate=nrm(e.plate||v?.plate||v?.code_label);
    const currentDept=deptCode(e.department_id||v?.department_id);
    const currentParking=(parkingOf(v)||parkingOfEvent(e))?.n||'';
    const plateRaw=prompt('Placa / código:',currentPlate);if(plateRaw===null)return;
    const plate=normalizePlateValue(plateRaw,e.vehicle_type||v?.vehicle_type);
    if(!plate){setMsg('msg','La placa/código no puede quedar vacío.');return}
    const deptRaw=prompt('Dpto. asociado:',currentDept);if(deptRaw===null)return;
    const department_id=await findDept(deptRaw);
    if(deptRaw.trim() && !department_id){setMsg('msg','El Dpto. indicado no existe.');return}
    const parkingRaw=prompt('Número de estacionamiento:',currentParking);if(parkingRaw===null)return;
    const parkingNumber=parseInt(parkingRaw,10);
    const ps=Number.isFinite(parkingNumber)?parkingByNumber(parkingNumber):null;
    if(parkingRaw.trim() && !ps){setMsg('msg','El número de estacionamiento no existe en VERDI.');return}
    try{
      const updateEvent={plate,department_id:department_id||null};
      if(ps)updateEvent.parking_space_id=ps.id;else updateEvent.parking_space_id=null;
      let r=await sb.from('access_events').update(updateEvent).eq('id',id).eq('building_id',BUILDING_ID);
      if(r.error)throw r.error;
      if(v){
        const vd={plate,code_label:plate,department_id:department_id||null,authorized_parking_spaces:ps?String(ps.space_number):'',parking_basement:ps?(ps.basement||basement(ps.space_number)):null,parking_required:!!ps,parking_space_id:ps?ps.id:null};
        r=await sb.from('vehicles').update(vd).eq('id',v.id).eq('building_id',BUILDING_ID);if(r.error)throw r.error;
        r=await sb.from('access_events').update({plate,department_id:department_id||null,parking_space_id:ps?ps.id:null}).eq('vehicle_id',v.id).eq('building_id',BUILDING_ID);if(r.error)throw r.error;
        await sb.from('vehicle_parking_spaces').update({active:false}).eq('vehicle_id',v.id);
        if(ps)await sb.from('vehicle_parking_spaces').upsert({vehicle_id:v.id,parking_space_id:ps.id,active:true},{onConflict:'vehicle_id,parking_space_id'});
      }
      await audit('EDITAR','access_event',{id,plate,department_id,parking_space:ps?.space_number||null});
      await load();setMsg('msg','Actualización aplicada en BUSCAR/DATA, DENTRO, SALIERON y PERMANENCIAS.',true);
    }catch(err){console.error('Editar permanencia:',err);setMsg('msg','No se pudo actualizar: '+(err.message||err))}
  };

  // ENTRÓ desde SALIERON: inserción directa y verificación de que realmente quedó grabada.
  window.registerEntryFromExit=async function(id){
    try{
      const e=(events||[]).find(x=>x.id===id);if(!e){setMsg('msg','No se encontró la salida.');return}
      const v=vehicleForEvent(e);if(!v){setMsg('msg','El vehículo ya no está en la base activa.');return}
      if((events||[]).filter(x=>x.vehicle_id===v.id).slice(-1)[0]?.movement==='entrada'){await load();setMsg('msg','Este vehículo ya figura DENTRO.');return}
      const p=parkingOf(v)||parkingOfEvent(e);
      const ins={vehicle_id:v.id,visitor_id:e.visitor_id||null,department_id:v.department_id||e.department_id||null,person_id:e.person_id||v.person_id||null,plate:nrm(v.plate||e.plate||v.code_label),vehicle_type:v.vehicle_type||e.vehicle_type||null,description:v.description||e.description||null,worker_name:user?.email||profile?.email||null,movement:'entrada',source_type:'manual',building_id:BUILDING_ID,parking_space_id:p?.n?parkingByNumber(p.n)?.id:null};
      let r=await sb.from('access_events').insert(ins).select().single();if(r.error)throw r.error;
      await load();
      const saved=(events||[]).find(x=>x.id===r.data?.id)|| (events||[]).filter(x=>x.vehicle_id===v.id).slice(-1)[0];
      if(!saved||saved.movement!=='entrada')throw new Error('Supabase no confirmó el ingreso.');
      setMsg('msg','Ingreso registrado correctamente.',true);
    }catch(err){console.error('ENTRÓ desde SALIERON:',err);setMsg('msg','No se pudo registrar el ingreso: '+(err.message||err))}
  };

  const oldRender=window.render;
  window.render=function(){
    oldRender();
    setHistHeaders();
    // Mantener los datos de PERMANENCIAS editables visibles y consistentes.
    const hist=(events||[]).slice().reverse().filter(e=>{
      const v=vehicleForEvent(e),dq=norm($('histDept')?.value),pq=norm($('histPlate')?.value),d=norm(deptCode(e.department_id||v?.department_id)),plate=norm(e.plate||v?.plate||v?.code_label);
      return (!dq||d.includes(dq))&&(!pq||plate===pq);
    });
    const hl=$('histList');
    if(hl)hl.innerHTML=hist.map(e=>{const v=vehicleForEvent(e),p=parkingOf(v)||parkingOfEvent(e),a=canAdmin()?'<button class="btn" style="width:auto;margin-right:4px" onclick="editAccessEvent(\''+e.id+'\')">Editar</button><button class="btn danger" style="width:auto" onclick="deleteAccessEvent(\''+e.id+'\')">Eliminar</button>':'';return '<tr><td>'+esc(deptCode(e.department_id||v?.department_id))+'</td><td>'+esc(nrm(e.plate||v?.plate||v?.code_label))+'</td><td>'+typeName(e.vehicle_type||v?.vehicle_type)+'</td><td>'+esc(e.movement||'')+'</td><td>'+new Date(e.event_time).toLocaleString('es-PE')+'</td><td>'+esc(p?('Cochera '+p.n+' — '+p.s):'—')+'</td><td>'+a+'</td></tr>'}).join('');
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
