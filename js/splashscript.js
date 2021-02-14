// Called to close after internal processing
function GoodFile() {
    document.getElementById("ID").submit();
}
function BadFile(name,msg) {
    alert("File "+name+" cannot be understood as a First Choice database.\n"+msg)
    document.getElementById("button").value="Intro"
    document.getElementById("ID").submit();
}
