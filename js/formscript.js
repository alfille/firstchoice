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
function showDialog() {
    document.getElementById("searchdialog").style.display = "block";
    Able("fschoose",true);
    Able("searchnameok",false);
    Able("fsnames",true);
    Able("SCSelect",false);
    Able("SCRename",false);
    Able("SCDelete",false);
};
function hideDialog() {
    document.getElementById("searchdialog").style.display = "none";
};
function TableChooseChanger() {
    Able("fsnames",false);
    Able("SCSelect",true);
    Able("SCRename",true);
    Able("SCDelete",true);
};
function SearchChoose( ) {
    document.getElementById("search_type").value = "choose";
    document.getElementById("search_0").value = document.getElementById("searchchoose").value;
    document.getElementById("search_back").submit();
    }
function SearchRename( ) {
    var d = document.getElementById("serchchoose").value;
    var x = prompt("Rename this search?",d);
    if ( x != null ) {
        document.getElementById("search_type").value = "srename";
        document.getElementById("search_0").value = d;
        document.getElementById("search_1").value = x;
        document.getElementById("search_back").submit();
        }
    }
function SearchDelete( ) {
    var d = document.getElementById("searchchoose").value;
    var x = confirm("Do you want to delete the '" + d +"' search?");
    if ( x == true ) {
        document.getElementById("search_type").value = "sremove";
        document.getElementById("search_0").value = d;
        document.getElementById("search_back").submit();
        }
    }
function NameChanger() {
    Able("fschoose",false);
    Able("searchnameok",true);
    }
function SearchName( ) {
    document.getElementById("search_type").value = "name";
    document.getElementById("search_0").value = document.getElementById("searchname").value;
    document.getElementById("search_back").submit();
    }

