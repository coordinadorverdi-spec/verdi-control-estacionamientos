from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v16 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v16 -->
<script>
(function(){
  // Buscar/Base: show only the corrected sortable list; the original duplicate list is hidden.
  const fl=$('findList');
  if(fl) fl.style.display='none';

  function latest(v){return events.filter(e=>e.vehicle_id===v.id).slice(-1)[0]}
  function history(v){return events.filter(e=>e.vehicle_id===v.id)}
  function frequent(v){return !!v.is_frequent}
  function insideNow(v){return latest(v)?.movement==='entrada'}
  function firstFrequentRegistration(v){return frequent(v)&&history(v).length===1&&latest(v)?.movement==='entrada'}
  const esc=x=>String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park=v=>String(v?.authorized_parking_spaces||'').trim()||'—';
  const bas=v=>v?.parking_basement||((park(v).split(',')[0]&&typeof basementFor==='function')?basementFor(park(v).split(',')[0]):'—');
  const d=v=>deptCode(v.department_id);

  function rebuild(){
    // Normal plates: first registration already creates their initial entry, so they appear DENTRO.
    // Frequent plates: their first registration is only the control record; they appear SALIERON
    // until the worker presses ENTRÓ for the first real building entry.
    const il=$('insideList');
    if(il) il.innerHTML=vehicles.filter(v=>insideNow(v)&&!firstFrequentRegistration(v)).map(v=>`<div class="row in"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(park(v))} ${esc(bas(v))}</span><button class="btn" onclick="move('salida','${v.id}')">SALIÓ</button></div>`).join('')||'No hay vehículos dentro.';

    const outs=vehicles.filter(v=>{
      if(firstFrequentRegistration(v)) return true;
      return latest(v)?.movement==='salida';
    }).sort((a,b)=>new Date(latest(b)?.event_time||0)-new Date(latest(a)?.event_time||0));
    const rl=$('recentList');
    if(rl) rl.innerHTML=outs.map(v=>`<div class="row out"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(park(v))} ${esc(bas(v))}</span><button class="btn" onclick="move('entrada','${v.id}')">ENTRÓ</button></div>`).join('')||'No hay vehículos que hayan salido.';

    const vl=$('visitList');
    if(vl) vl.innerHTML=vehicles.filter(frequent).map(v=>`<div class="row"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(v.responsible_name||'—')} · ${esc(relName(v.relationship))}</span><span style="display:flex;gap:6px;width:100%;max-width:210px"><button class="btn" onclick="editFrequent('${v.id}')">EDITAR</button><button class="btn danger" onclick="deleteFrequent('${v.id}')">ELIMINAR</button></span></div>`).join('')||'No hay visitas frecuentes.';

    // v15 already renders the corrected Base list; keep it as the sole visible list.
  }

  const previousRender=window.render;
  window.render=function(){try{if(previousRender)previousRender()}catch(e){};rebuild()};
  setTimeout(rebuild,350);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
