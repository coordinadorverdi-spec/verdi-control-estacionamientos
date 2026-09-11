from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v18 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v18 -->
<script>
(function(){
  const esc18=x=>String(x??'').replace(/[&<>\\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
  const park18=v=>String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—';
  const dept18=v=>deptCode(v?.department_id);
  const basement18=v=>v?.parking_basement||((park18(v)!=='—'&&typeof basementFor==='function')?basementFor(park18(v)):'—');
  const rel18=x=>({propietario_dpto:'Propietario',inquilino_dpto:'Inquilino',propietario_cochera:'Propietario cochera',inquilino_externo:'Inquilino externo',visita:'Visita'})[x]||x||'—';
  const active18=v=>!v.deleted_at && !v.is_frequent;
  const box18=()=>document.getElementById('baseList');

  function renderBase18(){
    const box=box18(); if(!box)return;
    const q=String(document.getElementById('finder')?.value||'').trim().toLowerCase();
    const mode=window.__verdiBaseSort||'dept';
    let list=(vehicles||[]).filter(active18);
    if(q) list=list.filter(v=>[v.plate,v.code_label,dept18(v),v.responsible_name].filter(Boolean).join(' ').toLowerCase().includes(q));
    list.sort((a,b)=>{
      const aa=mode==='parking'?parseInt(park18(a),10)||9999:parseInt(dept18(a),10)||9999;
      const bb=mode==='parking'?parseInt(park18(b),10)||9999:parseInt(dept18(b),10)||9999;
      return aa-bb || String(a.plate||a.code_label||'').localeCompare(String(b.plate||b.code_label||''));
    });
    box.innerHTML=list.map(v=>`<div class="row v18base" style="display:block;padding:9px 6px;box-sizing:border-box;width:100%;overflow:hidden">
      <div style="display:flex;align-items:center;gap:5px;min-width:0;width:100%;white-space:nowrap;overflow:hidden">
        <span style="min-width:0;overflow:hidden;text-overflow:ellipsis"><b>${esc18(v.plate||v.code_label)}</b>•D ${esc18(dept18(v))}•${esc18(park18(v))}•${esc18(basement18(v))}</span>
      </div>
      <div style="display:flex;align-items:center;gap:5px;min-width:0;width:100%;white-space:nowrap;overflow:hidden;margin-top:2px">
        <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis">${esc18(v.responsible_name||'—')} - ${esc18(rel18(v.relationship))}</span>
        <button class="btn" style="padding:3px 7px;min-width:0" onclick="editBase17('${v.id}')">✎</button>
        <button class="btn danger" style="padding:3px 7px;min-width:0" onclick="deleteBase17('${v.id}')">×</button>
      </div>
    </div>`).join('')||'No hay registros.';
  }

  window.renderBase18=renderBase18;
  const oldRender18=window.render;
  window.render=function(){try{oldRender18()}catch(e){};renderBase18()};

  // Re-apply the compact two-line Base after any legacy render/load operation.
  const oldLoad18=window.load;
  window.load=async function(){await oldLoad18();renderBase18()};

  const box=box18();
  if(box){
    const mo=new MutationObserver(()=>{ if(!box.__v18busy){ clearTimeout(box.__v18timer); box.__v18timer=setTimeout(renderBase18,0); } });
    mo.observe(box,{childList:true,subtree:true});
  }
  const finder=document.getElementById('finder');
  if(finder) finder.addEventListener('input',renderBase18);
  setInterval(renderBase18,1500);
  setTimeout(renderBase18,300);
})();
</script>
<style>
#baseList .v18base{font-size:14px;line-height:1.2}
#baseList .v18base button{font-size:12px;line-height:1;height:26px}
@media(max-width:600px){#baseList .v18base{font-size:13px;padding:7px 4px!important}#baseList .v18base button{height:24px;padding:2px 6px!important}}
</style>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
