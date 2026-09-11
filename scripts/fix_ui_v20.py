from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v20 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v20 -->
<script>
(function(){
  const esc20=x=>String(x??'').replace(/[&<>\\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park20=v=>String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—';
  const dept20=v=>deptCode(v?.department_id);
  const basement20=v=>{const n=park20(v);if(n==='—')return '—';const ps=(spaces||[]).find(x=>String(x.space_number)===String(n));return ps?.basement||(typeof basementFor==='function'?basementFor(n):'—')};
  const type20=x=>({auto:'Auto',moto:'Moto',bicicleta:'Bicicleta',otro:'Otro'})[x]||x||'—';
  const isVisit20=v=>v?.is_frequent||v?.relationship==='visita';
  const fmt20=e=>new Date(e).toLocaleString('es-PE',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});
  const last20=v=>events.filter(e=>e.vehicle_id===v.id).sort((a,b)=>new Date(a.event_time)-new Date(b.event_time)).pop();

  function compactRow20(v,action){
    const b=basement20(v), p=park20(v), button=action==='S'?'<button class="v20move" onclick="move(\\'salida\\',\\''+v.id+'\\')">S</button>':'<button class="v20move" onclick="move(\\'entrada\\',\\''+v.id+'\\')">E</button>';
    return '<div class="v20row"><div class="v20line1"><b>'+esc20(v.plate||v.code_label)+'</b> • D '+esc20(dept20(v))+' • '+esc20(p)+' • '+esc20(b)+'</div><div class="v20line2"><span>'+esc20(v.responsible_name||'—')+' - '+esc20(v.relationship==='visita'?'Visita':v.relationship||'—')+'</span>'+button+'</div></div>';
  }

  function renderInside20(){
    const box=document.getElementById('insideList');if(!box)return;
    const list=(vehicles||[]).filter(v=>!v.deleted_at&&!v.is_frequent&&!isVisit20(v)&&inside(v));
    box.innerHTML=list.map(v=>compactRow20(v,'S')).join('')||'No hay vehículos dentro.';
  }

  function renderRecent20(){
    const box=document.getElementById('recentList');if(!box)return;
    const exited=new Set(events.filter(e=>e.movement==='salida').map(e=>e.vehicle_id));
    const list=(vehicles||[]).filter(v=>!v.deleted_at && (exited.has(v.id) || isVisit20(v)) && !inside(v));
    list.sort((a,b)=>{const ea=last20(a),eb=last20(b);return new Date(eb?.event_time||0)-new Date(ea?.event_time||0)});
    box.innerHTML=list.map(v=>compactRow20(v,'E')).join('')||'No hay vehículos para registrar entrada.';
  }

  function renderHist20(){
    const section=document.getElementById('hist');if(!section)return;
    const card=section.querySelector('.card');if(!card)return;
    let tools=document.getElementById('histFilters20');
    if(!tools){
      tools=document.createElement('div');tools.id='histFilters20';tools.innerHTML='<div class="v20filters"><select id="histDept20"><option value="">Todos los Dptos.</option></select><input id="histPlate20" placeholder="Filtrar por placa"><select id="histMove20"><option value="">Todos los movimientos</option><option value="entrada">Solo entradas</option><option value="salida">Solo salidas</option></select><button id="histAll20" class="btn">Ver todas las placas</button></div>';
      const csv=document.getElementById('csv'); if(csv) csv.insertAdjacentElement('afterend',tools); else card.insertBefore(tools,card.firstChild);
      document.getElementById('histDept20').addEventListener('change',renderHist20);
      document.getElementById('histPlate20').addEventListener('input',renderHist20);
      document.getElementById('histMove20').addEventListener('change',renderHist20);
      document.getElementById('histAll20').addEventListener('click',()=>{document.getElementById('histDept20').value='';document.getElementById('histPlate20').value='';document.getElementById('histMove20').value='';renderHist20()});
    }
    const ds=document.getElementById('histDept20');const cur=ds.value;ds.innerHTML='<option value="">Todos los Dptos.</option>'+(depts||[]).map(d=>'<option value="'+esc20(d.id)+'">D '+esc20(d.code)+'</option>').join('');ds.value=cur;
    const plate=(document.getElementById('histPlate20')?.value||'').trim().toLowerCase();const dept=document.getElementById('histDept20')?.value||'';const mov=document.getElementById('histMove20')?.value||'';
    const cutoff=Date.now()-60*24*60*60*1000;
    const list=(events||[]).filter(e=>new Date(e.event_time).getTime()>=cutoff && (!dept||e.department_id===dept) && (!plate||String(e.plate||'').toLowerCase().includes(plate)) && (!mov||e.movement===mov)).slice().sort((a,b)=>new Date(b.event_time)-new Date(a.event_time));
    const body=document.getElementById('histList');if(body)body.innerHTML=list.map(e=>'<tr><td>D '+esc20(deptCode(e.department_id))+'</td><td>'+esc20(e.plate||'—')+'</td><td>'+type20(e.vehicle_type)+'</td><td>'+esc20(e.movement==='entrada'?'ENTRÓ':'SALIÓ')+'</td><td>'+fmt20(e.event_time)+'</td><td>'+esc20(e.worker_name||'—')+'</td></tr>').join('')||'<tr><td colspan="6">No hay registros para el filtro seleccionado.</td></tr>';
  }

  function ensureHistStyles20(){
    if(document.getElementById('v20styles'))return;const st=document.createElement('style');st.id='v20styles';st.textContent=`
      #insideList .v20row,#recentList .v20row{display:block!important;padding:6px 4px;border-bottom:1px solid #eee;font-size:13px;line-height:1.15;overflow:hidden}
      .v20line1{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v20line2{display:flex;align-items:center;gap:7px;margin-top:2px;min-width:0}.v20line2 span{min-width:0;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v20move{width:30px!important;min-width:30px!important;height:25px;padding:0!important;border-radius:6px;border:0;background:#e6edf3;font-weight:bold;cursor:pointer}
      #histFilters20{margin:9px 0}.v20filters{display:grid;grid-template-columns:1fr 1fr 1fr auto;gap:6px;align-items:center}.v20filters input,.v20filters select,.v20filters button{margin:0;padding:8px;width:100%;min-width:0}
      #hist table{font-size:12px}@media(max-width:650px){.v20filters{grid-template-columns:1fr 1fr}.v20filters button{grid-column:1 / -1}.v20filters input,.v20filters select{font-size:12px;padding:8px}#insideList .v20row,#recentList .v20row{font-size:12.5px}}
    `;document.head.appendChild(st)
  }

  const oldRender20=window.render;window.render=function(){try{oldRender20()}catch(e){};ensureHistStyles20();renderInside20();renderRecent20();renderHist20()};
  const oldLoad20=window.load;window.load=async function(){await oldLoad20();ensureHistStyles20();renderInside20();renderRecent20();renderHist20()};
  setTimeout(()=>{ensureHistStyles20();renderInside20();renderRecent20();renderHist20()},700);

  // Daily cleanup: keep only the latest 60 days of movement history. The UI also hides anything older.
  async function purge20(){
    if(!user)return;const cutoff=new Date(Date.now()-60*24*60*60*1000).toISOString();
    try{const r=await sb.from('access_events').delete().eq('building_id',BUILDING_ID).lt('event_time',cutoff);if(r.error)console.warn('Permanencias cleanup:',r.error.message)}catch(e){console.warn('Permanencias cleanup:',e.message||e)}
  }
  setTimeout(purge20,1200);setInterval(purge20,24*60*60*1000);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
