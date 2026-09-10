from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v6 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v6 -->
<script>
(function(){
  const nrm=x=>String(x??'').trim().toUpperCase();
  const norm=x=>nrm(x).replace(/\s+/g,'');
  const basement=x=>{const n=parseInt(String(x??''),10);if(n>=1&&n<=43)return'S1';if(n<=89&&n>=44)return'S2';if(n<=136&&n>=90)return'S3';if(n<=147&&n>=137)return'S4';return'—'};
  const veh=e=>(vehicles||[]).find(v=>v.id===e?.vehicle_id)||null;
  const park=v=>{const a=[];String(v?.authorized_parking_spaces??'').split(',').map(x=>x.trim()).filter(Boolean).forEach(x=>a.push({n:x,s:basement(x)}));if(!a.length&&v?.parking_space_id){const p=(spaces||[]).find(x=>x.id===v.parking_space_id);if(p)a.push({n:p.space_number,s:p.basement||basement(p.space_number)})}return a[0]||null};
  const compact=(v,e)=>{const label=nrm(e?.plate||v?.plate||v?.code_label)||'—';const d=deptCode(e?.department_id||v?.department_id);const p=park(v);return label+' D. '+d+' - '+(p?p.n:'—')+' '+(p?p.s:'—')};
  const uniqueVehicles=list=>{const seen=new Set();return (list||[]).filter(v=>{const k=norm(v?.plate||v?.code_label);if(!k||seen.has(k))return false;seen.add(k);return true})};

  async function directEntry(id){
    try{
      const e=(events||[]).find(x=>x.id===id);if(!e){setMsg('msg','No se encontró la salida.');return}
      const v=veh(e);if(!v){setMsg('msg','La salida no tiene vehículo asociado.');return}
      if(inside(v)){setMsg('msg','Este vehículo ya figura DENTRO.');await load();return}
      const p=park(v);const ins={vehicle_id:v.id,visitor_id:e.visitor_id||null,department_id:e.department_id||v.department_id||null,person_id:e.person_id||v.person_id||null,plate:nrm(e.plate||v.plate||v.code_label),vehicle_type:e.vehicle_type||v.vehicle_type||null,description:e.description||v.description||null,worker_name:user?.email||profile?.email||null,movement:'entrada',source_type:'manual',building_id:BUILDING_ID};
      if(p){const ps=(spaces||[]).find(x=>String(x.space_number)===String(p.n));if(ps)ins.parking_space_id=ps.id}
      const r=await sb.from('access_events').insert(ins);if(r.error)throw r.error;
      await load();setMsg('msg','Ingreso registrado correctamente.',true);
    }catch(err){console.error('ENTRÓ:',err);setMsg('msg','No se pudo registrar el ingreso: '+(err.message||err))}
  }
  window.registerEntryFromExit=directEntry;

  function ensureHistControls(){
    const sec=$('hist');if(!sec)return;
    let box=$('histFilters');
    if(!box){box=document.createElement('div');box.id='histFilters';box.style.margin='10px 0';box.innerHTML='<input id="histDept" autocomplete="off" placeholder="Filtrar por Dpto."><select id="histPlate"><option value="">Todas las placas</option></select>';sec.querySelector('h2')?.after(box)}
    const di=$('histDept'),ps=$('histPlate');
    if(di&&!di.dataset.bound){di.dataset.bound='1';di.addEventListener('input',updateHistPlateOptions)}
    if(ps&&!ps.dataset.bound){ps.dataset.bound='1';ps.addEventListener('change',window.render)}
    updateHistPlateOptions();
  }
  function updateHistPlateOptions(){
    const di=$('histDept'),ps=$('histPlate');if(!di||!ps)return;
    const q=norm(di.value);const rows=(events||[]).map(e=>({e,v:veh(e)})).filter(x=>!q||norm(deptCode(x.e.department_id||x.v?.department_id)).includes(q));
    const vals=[];const seen=new Set();rows.forEach(x=>{const val=nrm(x.e.plate||x.v?.plate||x.v?.code_label);const k=norm(val);if(val&&!seen.has(k)){seen.add(k);vals.push(val)}});
    const old=ps.value;ps.innerHTML='<option value="">Todas las placas</option>'+vals.sort().map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('');if(vals.includes(old))ps.value=old;
  }
  function matchesHist(e){const v=veh(e),dq=norm($('histDept')?.value),pq=norm($('histPlate')?.value);const d=norm(deptCode(e.department_id||v?.department_id));const plate=norm(e.plate||v?.plate||v?.code_label);return (!dq||d.includes(dq))&&(!pq||plate===pq)}

  const oldRender=window.render;
  window.render=function(){
    oldRender();
    ensureHistControls();
    updateHistPlateOptions();
    const iq=norm($('insideFilter')?.value),rq=norm($('recentFilter')?.value);
    const insideList=uniqueVehicles((vehicles||[]).filter(inside).filter(v=>!iq||[v.plate,v.code_label,deptCode(v.department_id),v.authorized_parking_spaces].filter(Boolean).join(' ').toUpperCase().includes(iq)));
    const il=$('insideList');if(il)il.innerHTML=insideList.map(v=>'<div class="row in compact-row"><span><b>'+esc(compact(v,{}))+'</b></span><button class="btn" style="width:auto" onclick="move(\'salida\',\''+v.id+'\')">[S]</button></div>').join('')||'No hay vehículos dentro.';
    const seenOut=new Set();const outs=(events||[]).filter(e=>e.movement==='salida').slice().reverse().filter(e=>{const v=veh(e),k=norm(e.plate||v?.plate||v?.code_label);if(!k||seenOut.has(k))return false;if(rq&&![e.plate,v?.plate,v?.code_label,deptCode(e.department_id||v?.department_id),v?.authorized_parking_spaces].filter(Boolean).join(' ').toUpperCase().includes(rq))return false;seenOut.add(k);return true}).slice(0,100);
    const rl=$('recentList');if(rl)rl.innerHTML=outs.map(e=>{const v=veh(e);return '<div class="row out compact-row"><span><b>'+esc(compact(v||{},e))+'</b></span><button class="btn primary" style="width:auto" onclick="registerEntryFromExit(\''+e.id+'\')">[E]</button></div>'}).join('')||'No hay salidas que coincidan.';
    const hist=(events||[]).slice().reverse().filter(matchesHist);const hl=$('histList');if(hl)hl.innerHTML=hist.map(e=>{const v=veh(e),a=canAdmin()?'<button class="btn" style="width:auto;margin-right:4px" onclick="editAccessEvent(\''+e.id+'\')">Editar</button><button class="btn danger" style="width:auto" onclick="deleteAccessEvent(\''+e.id+'\')">Eliminar</button>':'';return '<tr><td>'+esc(deptCode(e.department_id||v?.department_id))+'</td><td>'+esc(nrm(e.plate||v?.plate||v?.code_label))+'</td><td>'+typeName(e.vehicle_type||v?.vehicle_type)+'</td><td>'+esc(e.movement||'')+'</td><td>'+new Date(e.event_time).toLocaleString('es-PE')+'</td><td>'+esc((park(v)||{}).n?('Cochera '+(park(v)||{}).n+' — '+(park(v)||{}).s):'—')+'</td><td>'+a+'</td></tr>'}).join('');

    // BUSCAR / BASE: un solo registro por placa/código.
    const unique=uniqueVehicles(vehicles);
    const base=$('baseList');if(base){const q=norm($('finder')?.value);base.innerHTML=unique.filter(v=>!q||[v.plate,v.code_label,deptCode(v.department_id),v.responsible_name,v.authorized_parking_spaces].filter(Boolean).join(' ').toUpperCase().includes(q)).map(v=>'<div class="row"><span><b>'+esc(nrm(v.plate||v.code_label))+'</b> · '+typeName(v.vehicle_type)+'<br>'+esc(v.responsible_name||'—')+' · '+relName(v.relationship)+' · Dpto. '+deptCode(v.department_id)+'</span></div>').join('')||'Base vacía.'}
  };

  ensureHistControls();
  const finder=$('finder');if(finder&&!finder.dataset.v6){finder.dataset.v6='1';finder.addEventListener('input',window.render)}
  const css=document.createElement('style');css.textContent='.compact-row{flex-direction:row!important;align-items:center!important;white-space:nowrap}.compact-row .btn{flex:0 0 auto}.compact-row span{overflow:hidden;text-overflow:ellipsis}#histFilters{display:grid;grid-template-columns:1fr 1fr;gap:8px}';document.head.appendChild(css);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
