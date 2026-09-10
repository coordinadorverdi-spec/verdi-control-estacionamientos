from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v16 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v16 -->
<script>
(function(){
  // The original Buscar renderer and the corrected Base renderer were both visible.
  // Keep a single, corrected list and preserve the filter/sort controls.
  const fl=$('findList');
  if(fl){fl.style.display='none';}

  // Rebuild the operational lists with the intended initial state:
  // - Every newly registered normal plate starts in DENTRO so its first SALIÓ can be recorded.
  // - A frequent visitor with no access history starts in SALIERON so its first ENTRÓ can be recorded.
  // - Once a frequent visitor enters, it moves to DENTRO; after exiting it returns to SALIERON.
  const oldRenderV15=window.__verdiRenderV15;
  function latest(v){return events.filter(e=>e.vehicle_id===v.id).slice(-1)[0]}
  function ins(v){return latest(v)?.movement==='entrada'}
  function out(v){return latest(v)?.movement==='salida'}
  function freq(v){return !!v.is_frequent}
  const esc=x=>String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park=v=>String(v?.authorized_parking_spaces||'').trim()||'—';
  const bas=v=>v?.parking_basement||((park(v).split(',')[0]&&typeof basementFor==='function')?basementFor(park(v).split(',')[0]):'—');
  const d=v=>deptCode(v.department_id);

  function rebuild(){
    const il=$('insideList');
    if(il) il.innerHTML=vehicles.filter(v=>ins(v)).map(v=>`<div class="row in"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(park(v))} ${esc(bas(v))}</span><button class="btn" onclick="move('salida','${v.id}')">SALIÓ</button></div>`).join('')||'No hay vehículos dentro.';

    const outs=vehicles.filter(v=>freq(v)?(!latest(v)||out(v)):out(v)).sort((a,b)=>new Date(latest(b)?.event_time||0)-new Date(latest(a)?.event_time||0));
    const rl=$('recentList');
    if(rl) rl.innerHTML=outs.map(v=>`<div class="row out"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(park(v))} ${esc(bas(v))}</span><button class="btn" onclick="move('entrada','${v.id}')">ENTRÓ</button></div>`).join('')||'No hay vehículos que hayan salido.';

    // Keep the dedicated frequent-visit register, independently of DENTRO/SALIERON state.
    const vl=$('visitList');
    if(vl) vl.innerHTML=vehicles.filter(freq).map(v=>`<div class="row"><span><b>${esc(v.plate||v.code_label)}</b> · ${typeName(v.vehicle_type)}<br>D. ${esc(d(v))} · ${esc(v.responsible_name||'—')} · ${esc(relName(v.relationship))}</span><span style="display:flex;gap:6px;width:100%;max-width:210px"><button class="btn" onclick="editFrequent('${v.id}')">EDITAR</button><button class="btn danger" onclick="deleteFrequent('${v.id}')">ELIMINAR</button></span></div>`).join('')||'No hay visitas frecuentes.';

    if(typeof renderBaseV15==='function') renderBaseV15();
  }

  // Replace the v15 render wrapper so the corrected operational lists are used.
  const previousRender=window.render;
  window.render=function(){try{if(previousRender)previousRender()}catch(e){};rebuild()};
  setTimeout(rebuild,350);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
