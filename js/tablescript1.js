// Called before table creation
function Able(n,v) {
    var x=document.getElementById(n);
    if (x !==null) {x.disabled=!v}
    };
function chooseFunction(id) {
    document.getElementById("_ID").value = id;
    document.getElementById("ID").submit();
    }
function fResize( indx ) {
    document.getElementById("table_type").value = "resize";
    document.getElementById("table_0").value = indx;
    document.getElementById("table_1").value = this.outerWidth;
    document.getElementById("table_back").submit();
    }
function fMove( from, to ) {
    document.getElementById("table_type").value = "move";
    document.getElementById("table_0").value = from;
    document.getElementById("table_1").value = to;
    document.getElementById("table_back").submit();
    }
function fSelect( indx ) {
    document.getElementById("table_type").value = "select";
    let values = [];
    document.querySelectorAll(`input[name="dfield"]:checked`).forEach((checkbox) => {
        values.push(checkbox.value);
    });
    document.getElementById("table_0").value = values;
    document.getElementById("table_back").submit();
    }
function fRestore( field ) {
    document.getElementById("table_type").value = "restore";
    document.getElementById("table_0").value = field;
    document.getElementById("table_back").submit();
    }
function fReset( ) {
    document.getElementById("table_type").value = "reset";
    document.getElementById("table_back").submit();
    }
function fCancel( ) {
    document.getElementById("table_type").value = "cancel";
    document.getElementById("table_back").submit();
    }
function TableChoose( ) {
    document.getElementById("table_type").value = "choose";
    document.getElementById("table_0").value = document.getElementById("tablechoose").value;
    document.getElementById("table_back").submit();
    }
function TableName( ) {
    document.getElementById("table_type").value = "name";
    document.getElementById("table_0").value = document.getElementById("tablename").value;
    document.getElementById("table_back").submit();
    }
function drop(event,to) {
    event.preventDefault();
    var from = event.dataTransfer.getData("Text");
    fMove( from, to.toString() ) ;
    }
function dragStart(event,n) {
    document.getElementById("status").innerHTML = "Moving a column position"
    event.dataTransfer.setData("text",n.toString())
    }
function dragEnd(event) {
    document.getElementById("status").innerHTML = ""
    }
function allowDrop(event) {
    event.preventDefault();
}
function FieldChanger() {
    Able("fschoose",false);
    Able("fsnames",false);
    Able("tablefieldok",true);
    }
function TableChooseChanger() {
    Able("fsnames",false);
    Able("fsfields",false);
    Able("TCSelect",true);
    Able("TCRename",true);
    Able("TCDelete",true);
    }
function NameChanger() {
    Able("fschoose",false);
    Able("fsfields",false);
    Able("tablenameok",true);
    }
function TableRename( ) {
    var d = document.getElementById("tablechoose").value;
    var x = prompt("Rename this table format?",d);
    if ( x != null ) {
        document.getElementById("table_type").value = "trename";
        document.getElementById("table_0").value = d;
        document.getElementById("table_1").value = x;
        document.getElementById("table_back").submit();
        }
    }
function TableDelete( ) {
    var d = document.getElementById("tablechoose").value;
    var x = confirm("Do you want to delete the '" + d +"' table format?");
    if ( x == true ) {
        document.getElementById("table_type").value = "tremove";
        document.getElementById("table_0").value = d;
        document.getElementById("table_back").submit();
        }
    }
function showDialog() {
    document.getElementById("tabledialog").style.display = "block";
    }
// Observe column widths
for (th of document.getElementsByClassName("thead")) {
    widths.push(0)
    ro.observe(th);
    }

