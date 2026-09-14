from pathlib import Path
p=Path('index.html'); s=p.read_text(encoding='utf-8'); marker='<!-- Verdi UI correction patch v23 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v23 -->
<script>
(function(){
const esc23=x=>String(x??'').replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\\':'\\','"':'&quot;'}[m]));
const park23=v=>String(v?.authorized_parking_spaces||'').split(',')[0].trim()||'—';
const dept23=v=>typeof deptCode==='function'?deptCode(v?.department_id):'—';
const bas23=v=>{const n=park23(v);if(n==='—')return '—';const p=(spaces||[]).find(x=>String(x.space_number)===n);return p?.basement||(typeof basementFor==='function'?basementFor(n):'—')};
const special23=v=>!!(v?.is_frequent||v?.relationship==='visita');
const last23=v=>(events||[]).filter(x=>x.vehicle_id===v.id).sort((a,b)=>new Date(a.event_time)-new Date(b.event_time)).pop();
function row23(v,k){const a=k==='S'?'salida':'entrada';const tag=v?.is_frequent?'VISITA FRECUENTE':(v?.relationship==='visita'?'VISITA':'');const b=k==='F'?'':'<button type="button" class="v23move" data-a="'+a+'" data-id="'+esc23(v.id)+'">'+k+'</button>';return '<div class="v23row"><div class="v23first"><span>'+(tag?'<span class="v23tag">'+tag+'</span> ':'')+'<b>'+esc23(v.plate||v.code_label)+'</b> • D '+esc23(dept23(v))+' • '+esc23(park23(v))+' • '+esc23(bas23(v))+'</span>'+b+'</div>'+(k==='F'?'<div class="v23second">'+esc23(v.responsible_name||'—')+' - '+esc23(v.relationship==='visita'?'Visita':v.relationship||'—')+'</div>':'')+'</div>'}
function attach23(x){x.querySelectorAll('.v23move').forEach(b=>b.onclick=async()=>{b.disabled=true;try{await window.move(b.dataset.a,b.dataset.id)}finally{b.disabled=false}})}
function render23(){const i=document.getElementById('insideList');if(i){const l=(vehicles||[]).filter(v=>!v.deleted_at&&!v.is_frequent&&v.relationship!=='visita'&&(inside(v)||!(events||[]).some(e=>e.vehicle_id===v.id)));i.innerHTML=l.map(v=>row23(v,'S')).join('')||'No hay vehículos dentro.';attach23(i)}const r=document.getElementById('recentList');if(r){const ex=new Set((events||[]).filter(e=>e.movement==='salida').map(e=>e.vehicle_id));const l=(vehicles||[]).filter(v=>!v.deleted_at&&!inside(v)&&(special23(v)||ex.has(v.id))).sort((a,b)=>new Date(last23(b)?.event_time||0)-new Date(last23(a)?.event_time||0));r.innerHTML=l.map(v=>row23(v,'I')).join('')||'No hay vehículos para registrar ingreso.';attach23(r)}const f=document.getElementById('visitList');if(f){const l=(vehicles||[]).filter(v=>!v.deleted_at&&v.is_frequent);f.innerHTML=l.map(v=>row23(v,'F')).join('')||'No hay visitas frecuentes.'}}
async function load23(){const r=await Promise.all([sb.from('vehicles').select('*').eq('building_id',BUILDING_ID).order('created_at',{ascending:false}),sb.from('access_events').select('*').eq('building_id',BUILDING_ID).order('event_time',{ascending:true}),sb.from('parking_spaces').select('*').eq('building_id',BUILDING_ID).order('space_number'),sb.from('departments').select('*').eq('building_id',BUILDING_ID).order('code')]);for(const x of r)if(x.error)throw x.error;vehicles=r[0].data||[];events=r[1].data||[];spaces=r[2].data||[];depts=r[3].data||[];render23()}
const st=document.createElement('style');st.textContent='.v23row{padding:7px 4px;border-bottom:1px solid #eee;font-size:13px}.v23first{display:flex;align-items:center;gap:7px;min-height:34px}.v23first>span{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.v23move{width:34px!important;min-width:34px!important;height:34px!important;padding:0!important;border-radius:6px!important;font-weight:700!important}.v23second{font-size:12px;color:#64748b;margin-top:2px}.v23tag{background:#ffeb3b;color:#000;font-weight:800;padding:1px 4px;border-radius:3px}';document.head.appendChild(st);window.render=render23;window.load=load23;setTimeout(render23,1200)})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1);p.write_text(s,encoding='utf-8')
