function Submitter() {
    document.getElementById("ok").setAttribute("style","visibility:hidden");    
    document.getElementById("processing").innerHTML="Processing the database...";
    document.getElementById("ok").setAttribute("type","submit");
    document.getElementById("intro").submit();
};
