from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v17 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v17 -->
<script>
(function(){
  const esc17=x=>String(x??'').replace(/[&<>\\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park17=v=>String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—';
  const dept17=v=>deptCode(v?.department_id);
  const basement17=v=>v?.parking_basement||((park17(v)!=='—'&&typeof basementFor==='function')?basementFor(park17(v)):'—');
  const rel17=x=>({propietario_dpto:'Propietario',inquilino_dpto:'Inquilino',propietario_cochera:'Propietario cochera',inquilino_externo:'Inquilino externo',visita:'Visita'})[x]||x||'—';
  const active17=v=>!v.deleted_at && !v.is_frequent;

  function renderBase17(){
    const box=$('baseList'); if(!box)return;
    const q=String($('finder')?.value||'').trim().toLowerCase();
    const mode=window.__verdiBaseSort||'dept';
    let list=vehicles.filter(active17);
    if(q) list=list.filter(v=>[v.plate,v.code_label,dept17(v),v.responsible_name].filter(Boolean).join(' ').toLowerCase().includes(q));
    list.sort((a,b)=>{
      const aa=mode==='parking'?parseInt(park17(a),10)||9999:parseInt(dept17(a),10)||9999;
      const bb=mode==='parking'?parseInt(park17(b),10)||9999:parseInt(dept17(b),10)||9999;
      return aa-bb || String(a.plate||a.code_label||'').localeCompare(String(b.plate||b.code_label||''));
    });
    box.innerHTML=list.map(v=>`<div class="row" style="gap:8px"><span style="flex:1"><b>${esc17(v.plate||v.code_label)}</b>•D ${esc17(dept17(v))}•${esc17(park17(v))}•${esc17(basement17(v))}<br>${esc17(v.responsible_name||'—')} - ${esc17(rel17(v.relationship))}</span><span style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;min-width:150px"><button class="btn" onclick="editBase17('${v.id}')">EDITAR</button><button class="btn danger" onclick="deleteBase17('${v.id}')">ELIMINAR</button></span></div>`).join('')||'No hay registros.';
  }

  window.editBase17=async function(id){
    const v=vehicles.find(x=>x.id===id); if(!v)return;
    const plate=prompt('Placa / código:',v.plate||v.code_label||''); if(plate===null)return;
    const dept=prompt('Departamento:',dept17(v)==='—'?'':dept17(v)); if(dept===null)return;
    const parking=prompt('Cochera:',park17(v)==='—'?'':park17(v)); if(parking===null)return;
    const person=prompt('Encargado / responsable:',v.responsible_name||''); if(person===null)return;
    const rel=prompt('Relación (propietario_dpto / inquilino_dpto / propietario_cochera / inquilino_externo):',v.relationship||'propietario_dpto'); if(rel===null)return;
    const rawPlate=plate.trim().toUpperCase();
    if(!rawPlate){setMsg('msg','La placa / código no puede quedar vacío.');return}
    const did=await findDept(dept);
    if(dept.trim() && !did){setMsg('msg','El Dpto. indicado no existe en el edificio.');return}
    const num=parking.trim()?parseInt(parking,10):null;
    let ps=null;
    if(Number.isFinite(num)){ps=spaces.find(x=>Number(x.space_number)===num);if(!ps){setMsg('msg','La cochera indicada no existe.');return}}
    try{
      // Free previous active parking link and assign the new one without altering movement history.
      await sb.from('vehicle_parking_spaces').update({active:false}).eq('vehicle_id',id).eq('active',true);
      if(ps){
        const link=await sb.from('vehicle_parking_spaces').insert({vehicle_id:id,parking_space_id:ps.id,active:true,building_id:BUILDING_ID});
        if(link.error)throw link.error;
      }
      const upd=await sb.from('vehicles').update({plate:rawPlate,code_label:rawPlate,department_id:did||null,responsible_name:person.trim()||null,relationship:rel.trim()||null,parking_space_id:ps?.id||null,authorized_parking_spaces:ps?String(num):null,parking_basement:ps?.basement||null,parking_required:!!ps,updated_at:new Date().toISOString()}).eq('id',id).eq('building_id',BUILDING_ID);
      if(upd.error)throw upd.error;
      await audit('EDITAR','vehicle',{id,plate:rawPlate,department_id:did,parking:num,responsible_name:person.trim(),relationship:rel.trim()});
      await load();
      setMsg('msg','Registro actualizado correctamente.',true);
    }catch(e){setMsg('msg','No se pudo actualizar: '+(e.message||e))}
  };

  window.deleteBase17=async function(id){
    const v=vehicles.find(x=>x.id===id); if(!v)return;
    if(!confirm('¿Eliminar este registro de la Base del edificio? La placa dejará de estar activa en la Base y se conservará el historial.'))return;
    try{
      await sb.from('vehicle_parking_spaces').update({active:false}).eq('vehicle_id',id).eq('active',true);
      const upd=await sb.from('vehicles').update({deleted_at:new Date().toISOString(),parking_space_id:null,authorized_parking_spaces:null,parking_basement:null,parking_required:false,updated_at:new Date().toISOString()}).eq('id',id).eq('building_id',BUILDING_ID);
      if(upd.error)throw upd.error;
      await audit('ELIMINAR','vehicle',{id,plate:v.plate||v.code_label});
      await load();
      setMsg('msg','Registro eliminado de la Base. El historial se conserva.',true);
    }catch(e){setMsg('msg','No se pudo eliminar: '+(e.message||e))}
  };

  // Keep deleted records out of every operational/base view while retaining access history.
  const oldLoad17=window.load;
  window.load=async function(){
    await oldLoad17();
    vehicles=vehicles.filter(v=>!v.deleted_at);
    renderBase17();
  };

  // The Base is the single authoritative visual list and always uses the same compact format.
  const oldRender17=window.render;
  window.render=function(){try{oldRender17()}catch(e){};renderBase17()};

  // Replace the legacy find list entirely; Buscar filters the same Base list.
  const fl=$('findList'); if(fl) fl.style.display='none';
  const finder=$('finder');
  if(finder && !finder.__v17){
    finder.__v17=true;
    finder.addEventListener('input',()=>renderBase17());
  }
  const sd=$('sortDept'),sp=$('sortPark');
  if(sd)sd.onclick=()=>{window.__verdiBaseSort='dept';renderBase17()};
  if(sp)sp.onclick=()=>{window.__verdiBaseSort='parking';renderBase17()};

  setTimeout(renderBase17,500);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
