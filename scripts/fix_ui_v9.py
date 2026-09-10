from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v9 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v9 -->
<script>
(function(){
  // The file picker must not be interpreted as navigation. Keep the Administration
  // view active after the Android/browser file chooser returns.
  const excelInput=$('excelFile');
  if(excelInput){
    excelInput.addEventListener('click',e=>e.stopPropagation(),true);
    excelInput.addEventListener('change',e=>{
      e.stopPropagation();
      const f=excelInput.files?.[0];
      if(f) setMsg('importMsg','Archivo seleccionado: '+f.name,true);
      const b=document.querySelector('.tabs button[data-v="admin"]');
      if(b && canAdmin()) b.click();
    },true);
  }

  function keepAdmin(){
    const b=document.querySelector('.tabs button[data-v="admin"]');
    if(b && canAdmin()) b.click();
  }

  // Replace the previous import handler so the selected File object is consumed
  // directly and the Administration tab is restored after processing.
  async function importExcelFixed(){
    const input=$('excelFile'), file=input?.files?.[0];
    if(!file){setMsg('importMsg','Seleccione un archivo Excel.');keepAdmin();return}
    try{
      setMsg('importMsg','Procesando '+file.name+'...',true);
      const data=await file.arrayBuffer();
      const wb=XLSX.read(data,{type:'array'});
      const sheet=wb.Sheets[wb.SheetNames[0]];
      const rows=XLSX.utils.sheet_to_json(sheet,{defval:''});
      if(!rows.length){setMsg('importMsg','El archivo no contiene registros.');keepAdmin();return}
      let created=0,updated=0,skipped=0;
      for(const row of rows){
        const plate=String(row['Placa / código']??row.placa_codigo??row.placa??row.codigo??'').trim().toUpperCase();
        if(!plate||plate.startsWith('EJEMPLO:')){skipped++;continue}
        const dq=normalizeDept(row['Dpto']??row.dpto??row.departamento??'');
        let did=null;
        if(dq){
          let d=(depts||[]).find(x=>normalizeDept(x.code)===dq);
          if(d)did=d.id;
          else{
            const q=await sb.from('departments').select('id,code').eq('building_id',BUILDING_ID).ilike('code',dq).maybeSingle();
            if(q.error)throw q.error;
            if(q.data){did=q.data.id;depts.push(q.data)}
            else{
              const ins=await sb.from('departments').insert({code:dq,building_id:BUILDING_ID}).select().single();
              if(ins.error)throw ins.error;did=ins.data.id;depts.push(ins.data)
            }
          }
        }
        const person=String(row['Persona asociada']??row.persona_asociada??row.responsable??'').trim();
        const relationship=String(row['Relación']??row.relacion??'').toLowerCase().includes('inquilino')?(String(row['Relación']??row.relacion).toLowerCase().includes('extern')?'inquilino_externo':'inquilino_dpto'):(String(row['Relación']??row.relacion).toLowerCase().includes('cochera')?'propietario_cochera':String(row['Relación']??row.relacion).toLowerCase().includes('visita')?'visita':'propietario_dpto');
        const kind=String(row['Tipo']??row.tipo??'').toLowerCase();
        const vehicle_type=kind.includes('moto')?'moto':kind.includes('bicic')?'bicicleta':kind.includes('otro')?'otro':'auto';
        const frequent=['SI','SÍ','YES','TRUE','1','X'].includes(String(row['Visita frecuente']??row.visita_frecuente??'').trim().toUpperCase());
        const basement=String(row['Sótano']??row.sotano??'').trim().toUpperCase();
        const parkingRaw=String(row['Cocheras']??row.cocheras??'').trim();
        const obs=String(row['Observaciones']??row.observaciones??'').trim();
        const existing=(vehicles||[]).find(x=>String(x.plate||x.code_label||'').toUpperCase()===plate);
        const payload={plate,code_label:plate,responsible_name:person||null,relationship,vehicle_type,department_id:did,is_frequent:frequent,parking_required:!!parkingRaw,parking_basement:basement||null,authorized_parking_spaces:parkingRaw||null,description:obs||null,building_id:BUILDING_ID};
        let veh;
        if(existing){const up=await sb.from('vehicles').update(payload).eq('id',existing.id).select().single();if(up.error)throw up.error;veh=up.data;updated++}
        else{const ins=await sb.from('vehicles').insert(payload).select().single();if(ins.error)throw ins.error;veh=ins.data;created++}
        // Keep parking relations consistent with the master vehicle data.
        await sb.from('vehicle_parking_spaces').update({active:false}).eq('vehicle_id',veh.id);
        for(const n of parkingRaw.split(',').map(x=>parseInt(x.trim(),10)).filter(Number.isFinite)){
          const ps=(spaces||[]).find(x=>Number(x.space_number)===n);
          if(ps){
            const up=await sb.from('vehicle_parking_spaces').upsert({vehicle_id:veh.id,parking_space_id:ps.id,active:true},{onConflict:'vehicle_id,parking_space_id'});
            if(up.error)throw up.error;
          }
        }
      }
      await load();
      keepAdmin();
      setMsg('importMsg',`Carga completada: ${created} nuevos, ${updated} actualizados, ${skipped} omitidos.`,true);
    }catch(e){console.error('Carga masiva:',e);keepAdmin();setMsg('importMsg','Error en la carga: '+(e.message||e))}
  }

  const importBtn=$('importExcel');
  if(importBtn) importBtn.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();importExcelFixed()},true);

  // ENTRÓ from SALIERON: use the same valid source_type as the original exit
  // event. The previous patch used "manual", which is not an allowed value in
  // the access_events constraint and therefore the INSERT was rejected.
  window.registerEntryFromExit=async function(id){
    try{
      const e=(events||[]).find(x=>x.id===id);if(!e){setMsg('msg','No se encontró la salida.');return}
      const v=(vehicles||[]).find(x=>x.id===e.vehicle_id);if(!v){setMsg('msg','El vehículo ya no está en la base activa.');return}
      const last=(events||[]).filter(x=>x.vehicle_id===v.id).slice(-1)[0];
      if(last?.movement==='entrada'){await load();setMsg('msg','Este vehículo ya figura DENTRO.');return}
      const p=(function(){
        const raw=String(v.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean)[0];
        if(raw){const ps=(spaces||[]).find(x=>String(x.space_number)===raw);if(ps)return ps}
        if(v.parking_space_id){const ps=(spaces||[]).find(x=>x.id===v.parking_space_id);if(ps)return ps}
        return e.parking_space_id?(spaces||[]).find(x=>x.id===e.parking_space_id):null;
      })();
      const ins={vehicle_id:v.id,visitor_id:e.visitor_id||null,department_id:v.department_id||e.department_id||null,person_id:e.person_id||v.person_id||null,plate:String(v.plate||e.plate||v.code_label||'').toUpperCase(),vehicle_type:v.vehicle_type||e.vehicle_type||null,description:v.description||e.description||null,worker_name:user?.email||profile?.email||null,movement:'entrada',source_type:e.source_type||'residente',building_id:BUILDING_ID,parking_space_id:p?.id||null};
      let r=await sb.from('access_events').insert(ins).select().single();
      if(r.error)throw r.error;
      await load();
      const saved=(events||[]).find(x=>x.id===r.data?.id);
      if(!saved||saved.movement!=='entrada')throw new Error('Supabase no confirmó el ingreso.');
      setMsg('msg','Ingreso registrado correctamente.',true);
    }catch(err){console.error('ENTRÓ desde SALIERON:',err);setMsg('msg','No se pudo registrar el ingreso: '+(err.message||err))}
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
