function Submitter() {
    if (document.getElementById("user").value == "" ) {
        alert("User needs to be filled in")
    } else {
        document.getElementById("ok").setAttribute("style","visibility:hidden");    
        document.getElementById("processing").innerHTML="Processing the database...";
        document.getElementById("ok").setAttribute("type","submit");
        document.getElementById("intro").submit();
    }
};
