from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v13 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v13 -->
<script>
(function(){
  // A selected file is pending only until the explicit import finishes.
  // This prevents the mobile-picker fix from forcing ADMINISTRATION forever.
  const originalImport=window.importExcel;
  if(typeof originalImport==='function'){
    window.importExcel=async function(){
      const input=$('excelFile');
      window.__verdiSelectedExcel = input?.files?.[0] || window.__verdiSelectedExcel || null;
      try{
        await originalImport();
        // The import routine reloads the vehicle/event data. Any vehicle that
        // has never had a movement is treated as already inside after the
        // initial bulk load, so DENTRO reflects the imported building fleet.
        const pending=(vehicles||[]).filter(v=>!events.some(e=>e.vehicle_id===v.id));
        for(const v of pending){
          const rr=await sb.from('access_events').insert({
            vehicle_id:v.id,
            plate:v.plate||v.code_label,
            movement:'entrada',
            source_type:v.is_frequent?'frecuente':(v.relationship==='visita'?'visita':'residente'),
            department_id:v.department_id,
            vehicle_type:v.vehicle_type,
            worker_name:user?.email||null,
            client_event_id:crypto.randomUUID(),
            building_id:BUILDING_ID
          });
          if(rr.error) console.warn('Entrada inicial de carga:',rr.error.message);
        }
        if(pending.length){
          await load();
          setMsg('importMsg','Datos cargados correctamente. '+pending.length+' vehículos incorporados a DENTRO.',true);
        }
      }finally{
        // Important: once processing is complete, the picker must no longer
        // be considered pending. Otherwise focus events can return to ADMIN.
        window.__verdiSelectedExcel=null;
        if(input) input.value='';
        const admin=$('admin');
        if(admin && canAdmin()){
          document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
          admin.classList.add('on');
          document.querySelectorAll('.tabs button[data-v]').forEach(x=>x.classList.remove('on'));
          const tab=document.querySelector('.tabs button[data-v="admin"]');
          if(tab) tab.classList.add('on');
        }
      }
    };
  }
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
