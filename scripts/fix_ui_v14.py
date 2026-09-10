from pathlib import Path

p=Path('index.html')
s=p.read_text(encoding='utf-8')
marker='<!-- Verdi UI correction patch v14 -->'
if marker in s:
    raise SystemExit(0)
patch=r'''<!-- Verdi UI correction patch v14 -->
<script>
(function(){
  // Handle tab navigation in capture phase so legacy mobile/focus handlers
  // cannot redirect the user back to Administration after importing Excel.
  document.addEventListener('click',function(e){
    const b=e.target?.closest?.('.tabs button[data-v]');
    if(!b) return;
    const viewId=b.dataset.v;
    const view=$(viewId);
    if(!view) return;
    try{ if(typeof clearForm==='function') clearForm(); }catch(err){}
    document.querySelectorAll('.tabs button[data-v]').forEach(x=>x.classList.remove('on'));
    document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));
    b.classList.add('on');
    view.classList.add('on');
    e.preventDefault();
    e.stopImmediatePropagation();
  },true);

  // A file is no longer pending once the import has completed. Keep this
  // state explicit for Android browsers that fire focus events unexpectedly.
  window.__verdiSelectedExcel=null;
  window.__verdiExcelImporting=false;
})();
</script>
'''
s=s.replace('</body>',patch+'\n</body>',1)
p.write_text(s,encoding='utf-8')
