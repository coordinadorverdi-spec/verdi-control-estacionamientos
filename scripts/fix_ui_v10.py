from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v10 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v10 -->
<script>
(function(){
  const baseRender=window.render;
  const keyPlate=v=>String(v?.plate||v?.code_label||'').trim().toUpperCase();
  const latestEventFor=v=>events.filter(e=>e.vehicle_id===v.id).slice().sort((a,b)=>new Date(b.event_time)-new Date(a.event_time))[0]||null;
  const dedupeVehicles=list=>{
    const m=new Map();
    for(const v of list){
      const k=keyPlate(v)||('ID:'+v.id), old=m.get(k);
      if(!old || new Date(v.updated_at||v.created_at||0)>new Date(old.updated_at||old.created_at||0))m.set(k,v);
    }
    return [...m.values()];
  };
  window.render=function(){
    if(typeof baseRender==='function') baseRender();
    const insideVehicles=dedupeVehicles(vehicles.filter(v=>inside(v)));
    $('insideList').innerHTML=insideVehicles.map(v=>{
      const p=parkingOf(v), park=p?(' - '+p.n+' '+p.s):'';
      return '<div class="row in"><span><b>'+esc(keyPlate(v))+'</b> D. '+esc(deptCode(v.department_id))+park+'</span><button class="btn" style="width:auto" onclick="move(\\'salida\\',\\''+v.id+'\\')">SALIÓ</button></div>';
    }).join('')||'No hay vehículos dentro.';

    // SALIERON shows only the latest exit for each vehicle/plate. If a new
    // ENTRADA is recorded, that vehicle is no longer shown here.
    const candidates=new Map();
    for(const e of events){
      if(e.movement!=='salida') continue;
      const v=vehicles.find(x=>x.id===e.vehicle_id); if(!v) continue;
      const k=keyPlate(v)||keyPlate(e)||('ID:'+e.vehicle_id), old=candidates.get(k);
      if(!old || new Date(e.event_time)>new Date(old.event_time)) candidates.set(k,e);
    }
    const outs=[...candidates.values()].filter(e=>{
      const v=vehicles.find(x=>x.id===e.vehicle_id), last=v?latestEventFor(v):null;
      return last?.id===e.id && last?.movement==='salida';
    }).sort((a,b)=>new Date(b.event_time)-new Date(a.event_time)).slice(0,30);
    $('recentList').innerHTML=outs.map(e=>{
      const v=vehicles.find(x=>x.id===e.vehicle_id), p=parkingOf(v)||parkingOfEvent(e), park=p?(' - '+p.n+' '+p.s):'';
      return '<div class="row out"><span><b>'+esc(keyPlate(v)||e.plate||'—')+'</b> D. '+esc(deptCode(v?.department_id||e.department_id))+park+'</span><button class="btn" style="width:auto" onclick="registerEntryFromExit(\\''+e.id+'\\')">[E]</button></div>';
    }).join('')||'No hay salidas recientes.';
  };
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
