function changeToTime() {
    console.log("jes");
    document.getElementById('id_time').type = 'time';
    document.getElementById('id_time').value = '20:00';

}

function removeFields() {
    var type = this.value
    if (type == "ELIMINATION") {
        console.log("jes");
        document.getElementById("id_num_of_groups").style.display = 'none';
        document.getElementById("id_teams_promoted").style.display = 'none';
        document.querySelector("label[for='id_num_of_groups']").style.display = 'none';
        document.querySelector("label[for='id_teams_promoted']").style.display = 'none';
    } else {
        document.getElementById("id_num_of_groups").style.display = 'block';
        document.getElementById("id_teams_promoted").style.display = 'block';
        document.querySelector("label[for='id_num_of_groups']").style.display = 'block';
        document.querySelector("label[for='id_teams_promoted']").style.display = 'block';
    }

}
document.getElementById("id_type").addEventListener('change', removeFields, false);
document.getElementById("id_type").addEventListener('load', removeFields, false);