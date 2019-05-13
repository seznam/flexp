
function annotate(obj) {
    form_id = $(obj).attr("id")
    $.post("/ajax", {action: "annotation_save",
                     value: obj.options[obj.selectedIndex].value,
                     id: form_id,
                     annotation_file: $(obj).attr('annotations_file')})
                .done(function(){

                })
                .fail(function(xhr, status, error){
                    alert(error)
                });
    document.getElementById("tr_"+form_id).style.backgroundColor = 'white';
    document.getElementById("tr_"+form_id).style.color = 'blue';
}