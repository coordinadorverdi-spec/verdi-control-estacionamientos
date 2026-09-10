from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v11 -->'
if marker in s: raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v11 -->
<script>
(function(){
  function showAdmin(){
    const admin=$('admin');
    if(!admin || !canAdmin()) return;
    document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
    admin.classList.add('on');
    document.querySelectorAll('.tabs button[data-v]').forEach(x=>x.classList.remove('on'));
    const tab=document.querySelector('.tabs button[data-v="admin"]');
    if(tab)tab.classList.add('on');
  }
  const input=$('excelFile');
  if(input){
    input.addEventListener('click',e=>{e.stopPropagation();showAdmin()},true);
    input.addEventListener('change',e=>{e.stopPropagation();showAdmin();
      const f=input.files?.[0];
      if(f) setMsg('importMsg','Archivo seleccionado: '+f.name,true);
    },true);
  }
  const btn=$('importExcel');
  if(btn)btn.addEventListener('click',e=>{e.stopPropagation();showAdmin()},true);
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
