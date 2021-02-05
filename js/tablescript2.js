// Call after column creation
function fColumns() {
    document.getElementById("table_type").value = "widths";
    var wid = [];
    for (const w of widths) {
        wid.push(Math.max(parseInt(w),10).toString()+"px");
    }
    document.getElementById("table_0").value = wid.toString();
    document.getElementById("table_back").submit();
    }
var widths=[]
var ro = new ResizeObserver(entrylist => {
  for (let entry of entrylist) {
    const cr = entry.contentRect;
    widths[parseInt(entry.target.getAttribute("data-n"))]=cr.width+2*cr.left;
  }
});
// Observe column widths
for (th of document.getElementsByClassName("thead")) {
    widths.push(0)
    ro.observe(th);
    }
