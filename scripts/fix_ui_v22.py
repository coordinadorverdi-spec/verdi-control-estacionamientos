from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v22 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v22 -->
<script>
(function(){
  function v22Park(v){return String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—'}
  function v22Basement(v){const n=v22Park(v);if(n==='—')return '—';const ps=(spaces||[]).find(x=>String(x.space_number)===String(n));return ps?.basement||(typeof basementFor==='function'?basementFor(n):'—')}
  function v22Dept(v){return typeof deptCode==='function'?deptCode(v?.department_id):'—'}
  function v22Esc(x){return String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]))}
  function v22Visit(v){return !!(v?.is_frequent||v?.relationship==='visita')}
  function v22Last(v){return (events||[]).filter(e=>e.vehicle_id===v.id).sort((a,b)=>new Date(a.event_time)-new Date(b.event_time)).pop()}
  function v22Attach(box){box.querySelectorAll('.v22move').forEach(b=>{b.onclick=async()=>{b.disabled=true;try{await window.move(b.dataset.action,b.dataset.id)}finally{b.disabled=false}}})}
  function v22Row(v,kind){
    const action=kind==='S'?'salida':'entrada';
    const button='<button type="button" class="v22move btn" data-action="'+action+'" data-id="'+v21Esc(v.id)+'">'+kind+'</button>';
    return '<div class="v22row"><span class="v22data"><b>'+v22Esc(v.plate||v.code_label)+'</b> • D '+v22Esc(v22Dept(v))+' • '+v22Esc(v22Park(v))+' • '+v22Esc(v22Basement(v))+'</span>'+button+(kind==='I'?'<div class="v22sub">'+v22Esc(v.responsible_name||'—')+' - '+v22Esc(v.relationship==='visita'?'Visita':v.relationship||'—')+'</div>':'')+'</div>';
  }
  function renderInside22(){
    const box=document.getElementById('insideList');if(!box)return;
    const list=(vehicles||[]).filter(v=>!v.deleted_at&&!v.is_frequent&&!v22Visit(v)&&(inside(v)||!(events||[]).some(e=>e.vehicle_id===v.id)));
    box.innerHTML=list.map(v=>v22Row(v,'S')).join('')||'No hay vehículos dentro.';
    v22Attach(box);
  }
  function renderRecent22(){
    const box=document.getElementById('recentList');if(!box)return;
    const exited=new Set((events||[]).filter(e=>e.movement==='salida').map(e=>e.vehicle_id));
    const list=(vehicles||[]).filter(v=>!v.deleted_at&&!inside(v)&&(v22Visit(v)||exited.has(v.id)));
    list.sort((a,b)=>new Date(v22Last(b)?.event_time||0)-new Date(v22Last(a)?.event_time||0));
    box.innerHTML=list.map(v=>v22Row(v,'I')).join('')||'No hay vehículos para registrar ingreso.';
    v22Attach(box);
  }
  const style=document.createElement('style');
  style.textContent='.v22row{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #eee;min-height:38px}.v22data{flex:1;min-width:0}.v22move{width:34px!important;height:34px!important;min-width:34px!important;padding:0!important;border-radius:6px!important;font-weight:700!important;line-height:1}.v22sub{width:100%;font-size:12px;color:#64748b;margin-top:2px}';
  document.head.appendChild(style);
  const oldRender22=window.render;
  window.render=function(){try{oldRender22()}catch(e){};renderInside22();renderRecent22()};
  const oldLoad22=window.load;
  window.load=async function(){await oldLoad22();renderInside22();renderRecent22()};
  setTimeout(()=>{renderInside22();renderRecent22()},900);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
