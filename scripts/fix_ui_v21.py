from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v21 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v21 -->
<script>
(function(){
  function v21Park(v){return String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—'}
  function v21Basement(v){const n=v21Park(v);if(n==='—')return '—';const ps=(spaces||[]).find(x=>String(x.space_number)===String(n));return ps?.basement||(typeof basementFor==='function'?basementFor(n):'—')}
  function v21Dept(v){return typeof deptCode==='function'?deptCode(v?.department_id):'—'}
  function v21Esc(x){return String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]))}
  function v21Visit(v){return !!(v?.is_frequent||v?.relationship==='visita')}
  function v21Last(v){return (events||[]).filter(e=>e.vehicle_id===v.id).sort((a,b)=>new Date(a.event_time)-new Date(b.event_time)).pop()}
  function v21Row(v,kind){
    const action=kind==='S'?'salida':'entrada';
    const button=kind==='S'?'<button class="v20move" onclick="move(\'salida\',\''+v.id+'\')">S</button>':'<button class="v20move" onclick="move(\'entrada\',\''+v.id+'\')">I</button>';
    return '<div class="v20row"><div class="v20line1"><b>'+v21Esc(v.plate||v.code_label)+'</b> • D '+v21Esc(v21Dept(v))+' • '+v21Esc(v21Park(v))+' • '+v21Esc(v21Basement(v))+'</div><div class="v20line2"><span>'+v21Esc(v.responsible_name||'—')+' - '+v21Esc(v.relationship==='visita'?'Visita':v.relationship||'—')+'</span>'+button+'</div></div>';
  }
  function renderInside21(){
    const box=document.getElementById('insideList');if(!box)return;
    // Every active non-visit vehicle starts in DENTRO. After SALIÓ it remains out until I is pressed.
    const list=(vehicles||[]).filter(v=>!v.deleted_at&&!v.is_frequent&&!v21Visit(v)&&(inside(v)||!(events||[]).some(e=>e.vehicle_id===v.id)));
    box.innerHTML=list.map(v=>v21Row(v,'S')).join('')||'No hay vehículos dentro.';
  }
  function renderRecent21(){
    const box=document.getElementById('recentList');if(!box)return;
    const exited=new Set((events||[]).filter(e=>e.movement==='salida').map(e=>e.vehicle_id));
    // Visits/frequent vehicles start in SALIERON; normal vehicles appear here only after their first SALIÓ.
    const list=(vehicles||[]).filter(v=>!v.deleted_at&&!inside(v)&&(v21Visit(v)||exited.has(v.id)));
    list.sort((a,b)=>new Date(v21Last(b)?.event_time||0)-new Date(v21Last(a)?.event_time||0));
    box.innerHTML=list.map(v=>v21Row(v,'I')).join('')||'No hay vehículos para registrar ingreso.';
  }
  const oldRender21=window.render;
  window.render=function(){try{oldRender21()}catch(e){};renderInside21();renderRecent21()};
  const oldLoad21=window.load;
  window.load=async function(){await oldLoad21();renderInside21();renderRecent21()};
  setTimeout(()=>{renderInside21();renderRecent21()},900);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
