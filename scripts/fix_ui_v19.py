from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v19 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v19 -->
<script>
(function(){
  const esc19=x=>String(x??'').replace(/[&<>\\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park19=v=>String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—';
  const dept19=v=>deptCode(v?.department_id);
  // The basement is derived from the selected parking space; users never need to enter S1-S4.
  const basement19=v=>{
    const n=park19(v);
    if(n==='—') return '—';
    const ps=(spaces||[]).find(x=>String(x.space_number)===String(n));
    return ps?.basement || (typeof basementFor==='function'?basementFor(n):'—');
  };
  const rel19=x=>({propietario_dpto:'Propietario',inquilino_dpto:'Inquilino',propietario_cochera:'Propietario cochera',inquilino_externo:'Inquilino externo',visita:'Visita'})[x]||x||'—';
  const active19=v=>!v.deleted_at && !v.is_frequent;

  function renderBase19(){
    const box=document.getElementById('baseList'); if(!box)return;
    const q=String(document.getElementById('finder')?.value||'').trim().toLowerCase();
    const mode=window.__verdiBaseSort||'dept';
    let list=(vehicles||[]).filter(active19);
    if(q) list=list.filter(v=>[v.plate,v.code_label,dept19(v),v.responsible_name].filter(Boolean).join(' ').toLowerCase().includes(q));
    // Preserve the existing BUSCAR/BASE sorting controls exactly as they are; only render their selected order.
    list.sort((a,b)=>{
      const aa=mode==='parking'?parseInt(park19(a),10)||9999:parseInt(dept19(a),10)||9999;
      const bb=mode==='parking'?parseInt(park19(b),10)||9999:parseInt(dept19(b),10)||9999;
      return aa-bb || String(a.plate||a.code_label||'').localeCompare(String(b.plate||b.code_label||''));
    });
    box.innerHTML=list.map(v=>`<div class="row v19base">
      <div class="v19main"><b>${esc19(v.plate||v.code_label)}</b> • D ${esc19(dept19(v))} • ${esc19(park19(v))} • ${esc19(basement19(v))}</div>
      <div class="v19sub"><button class="v19edit" aria-label="Editar registro" title="Editar" onclick="editBase17('${v.id}')">✎</button><span class="v19person">${esc19(v.responsible_name||'—')} - ${esc19(rel19(v.relationship))}</span><button class="v19delete" aria-label="Eliminar registro" title="Eliminar" onclick="deleteBase17('${v.id}')">×</button></div>
    </div>`).join('')||'No hay registros.';
  }

  window.renderBase19=renderBase19;
  const oldRender19=window.render;
  window.render=function(){try{oldRender19()}catch(e){};renderBase19()};
  const oldLoad19=window.load;
  window.load=async function(){await oldLoad19();renderBase19()};

  // Keep the existing sort buttons untouched. They remain owned by v17 and only trigger a Base re-render.
  const finder=document.getElementById('finder');
  if(finder) finder.addEventListener('input',renderBase19);
  const box=document.getElementById('baseList');
  if(box){
    const mo=new MutationObserver(()=>{clearTimeout(box.__v19timer);box.__v19timer=setTimeout(renderBase19,0)});
    mo.observe(box,{childList:true,subtree:true});
  }
  setTimeout(renderBase19,300);
})();
</script>
<style>
#baseList .v19base{display:block!important;width:100%;box-sizing:border-box;padding:6px 4px!important;line-height:1.15;font-size:13px;overflow:hidden}
#baseList .v19main{display:block;width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#baseList .v19sub{display:grid;grid-template-columns:30px minmax(0,1fr) 30px;align-items:center;gap:6px;width:100%;margin-top:3px}
#baseList .v19person{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center}
#baseList .v19sub button{width:30px;height:26px;min-width:30px;padding:0!important;font-size:17px;line-height:24px;border-radius:6px;display:flex;align-items:center;justify-content:center}
#baseList .v19edit{justify-self:start}
#baseList .v19delete{justify-self:end}
@media(max-width:600px){#baseList .v19base{font-size:12.5px;padding:5px 2px!important}#baseList .v19sub{grid-template-columns:28px minmax(0,1fr) 28px;gap:5px}#baseList .v19sub button{width:28px;height:24px;min-width:28px;font-size:16px}}
</style>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
