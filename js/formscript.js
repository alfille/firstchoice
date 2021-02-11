function Able(n,v) {
    var x=document.getElementById(n);
    if (x !==null) {x.disabled=!v}
};
function ChangeData() {
    Able("add",true);
    Able("back",false);
    Able("copy",false);
    Able("delete",false);
    Able("clear",true);
    Able("next",false);
    Able("research",true);
    Able("reset",true);
    Able("save",true);
    Able("search",true);
};
function DeleteRecord() {
    var x = confirm("Do you want to delete the record?");
    var d = document.getElementById("delete");
    if ( x == true ) {
        d.setAttribute('type','submit');
        d.value = "Delete";
        document.getElementById("mainform").submit();
        }
};
function Intro() {
    document.getElementById("bintro").value = "Intro";
    document.getElementById("fintro").submit();
};
